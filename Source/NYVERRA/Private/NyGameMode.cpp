#include "NyGameMode.h"
#include "NyCharacter.h"
#include "NyResource.h"
#include "NyLootCrate.h"
#include "NyEnemy.h"
#include "NyHUD.h"
#include "NyWorldState.h"
#include "NyBuildPiece.h"
#include "NyBaseSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/GameStateBase.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/Pawn.h"
#include "EngineUtils.h"
#include "NavigationSystem.h"
#include "Engine/EngineTypes.h"
// Server-authoritative placement: use the collision surface, never client-only visuals.
static FVector NyServerGround(UWorld* World, const FVector& XY, float Offset)
{
 // Site architecture is generated independently on server and clients. Never
 // mistake its roofs/platforms for Landscape when determining spawn elevation.
 if (!World) return FVector(XY.X, XY.Y, Offset);
 FCollisionQueryParams Query(SCENE_QUERY_STAT(NySpawnGround), false);
 const FVector Start(XY.X, XY.Y, 50000.f);
 const FVector End(XY.X, XY.Y, -50000.f);
 for (int32 Attempt = 0; Attempt < 128; ++Attempt)
 {
  FHitResult Hit;
  if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Query)) break;
  AActor* Obstacle = Hit.GetActor();
  if (IsValid(Obstacle) && (Obstacle->ActorHasTag(TEXT("NYVERRA_SiteGeometry")) ||
       Obstacle->IsA<ANyResource>() || Obstacle->IsA<ANyLootCrate>() ||
       Obstacle->IsA<ANyEnemy>() || Obstacle->IsA<APawn>()))
  {
   Query.AddIgnoredActor(Obstacle);
   continue;
  }
  return FVector(XY.X, XY.Y, Hit.ImpactPoint.Z + Offset);
 }
 UE_LOG(LogTemp, Warning, TEXT("[NYVERRA 0.42] No landscape collision at XY=(%.0f,%.0f); using Z fallback"), XY.X, XY.Y);
 return FVector(XY.X, XY.Y, Offset);
}

ANyGameMode::ANyGameMode(){
 DefaultPawnClass=ANyCharacter::StaticClass();HUDClass=ANyHUD::StaticClass();GameStateClass=ANyWorldState::StaticClass();
}
// PlayerStart actors must be checked after the map actors have been loaded.
// InitGame runs too early to reliably see editor-authored PlayerStarts.
static void NyEnsureFallbackPlayerStarts(UWorld* World)
{
 if (!World || World->GetNetMode() == NM_Client) return;
 for (TActorIterator<APlayerStart> It(World); It; ++It)
 {
  UE_LOG(LogTemp, Display, TEXT("[NYVERRA 0.52] Using map-authored PlayerStarts"));
  return;
 }
 UE_LOG(LogTemp, Warning, TEXT("[NYVERRA 0.52] Map has no PlayerStart; creating temporary test spawns"));
 for (int32 Index=0; Index<8; ++Index)
 {
  const float Angle=2.f*PI*Index/8.f;
  const FVector Origin(FMath::Cos(Angle)*280.f,FMath::Sin(Angle)*280.f,0.f);
  World->SpawnActor<APlayerStart>(NyServerGround(World,Origin,125.f),FRotator(0, FMath::RadiansToDegrees(Angle),0));
 }
}
void ANyGameMode::BeginPlay(){
 Super::BeginPlay();
 if(HasAuthority()) {
  NyEnsureFallbackPlayerStarts(GetWorld());
  // A saved level must contain an editor-authored NavMeshBoundsVolume.
  // Runtime-spawned volumes cannot reliably guarantee built navigation on a packaged server.
  if(UNavigationSystemV1* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld())){
   if(!Nav->GetDefaultNavDataInstance(FNavigationSystem::DontCreate))
    UE_LOG(LogTemp,Warning,TEXT("[NYVERRA 0.16] No NavData: create a saved test map and add NavMeshBoundsVolume before testing PvE AI."));
  }
  SpawnServerResources(); SpawnSiteResources(); SpawnSiteLoot(); SpawnEnemies();
  // Restore existing bases only on non-PIE authoritative worlds.
  LoadBases();
  // In a listen server, the local player may log in BEFORE BeginPlay. Rebind
  // such players as well as later arrivals handled by PostLogin.
  if(AGameStateBase* State=GetWorld()->GetGameState()){
   for(APlayerState* Player:State->PlayerArray)
    BindPlayerToSavedBases(Player);
  }
  if(ShouldPersistBases()&&!bBaseSaveReadOnly)
   GetWorldTimerManager().SetTimer(BaseAutosaveTimer,this,
    &ANyGameMode::SaveBases,60.f,true);
 }
}
void ANyGameMode::SpawnServerResources(){
 UWorld* W=GetWorld();if(!W)return;
 FRandomStream R(94621);
 for(int32 i=0;i<120;i++){
  const FVector P(R.FRandRange(-3800,3800),R.FRandRange(-3800,3800),0);
  if(P.Size2D()<500)continue;
  // Preserve readable, navigable spaces in and around the three exploration sites.
  const FVector2D XY(P.X,P.Y);
  if(FVector2D::Distance(XY,FVector2D(1750.f,1550.f))<1150.f ||
     FVector2D::Distance(XY,FVector2D(-2050.f,900.f))<1300.f ||
     FVector2D::Distance(XY,FVector2D(450.f,-2350.f))<1050.f) continue;
  const ENyResourceKind Type=i%17==0?ENyResourceKind::Berries:
   i%13==0?ENyResourceKind::Water:
   i%11==0?ENyResourceKind::EchoShard:
   i%3==0?ENyResourceKind::Stone:ENyResourceKind::Wood;
  const float Z=Type==ENyResourceKind::Wood?80.f:Type==ENyResourceKind::Water?65.f:35.f;
  if(ANyResource* N=W->SpawnActor<ANyResource>(NyServerGround(W,P,Z),FRotator::ZeroRotator)){
   N->Setup(Type,Type==ENyResourceKind::EchoShard?3:
    Type==ENyResourceKind::Berries?4:Type==ENyResourceKind::Water?8:6);
  }
 }
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA Alpha 0.9] wilderness resource pool ready"));
}

// Deterministic points of interest: unlike decorative meshes, these are server-owned,
// replicated harvestable actors. Their locations are deliberately in open courtyards.
void ANyGameMode::SpawnSiteResources(){
 UWorld* W=GetWorld(); if(!W || !HasAuthority()) return;
 struct FSiteDrop { FVector Position; ENyResourceKind Kind; int32 Amount; };
 const FSiteDrop Drops[] = {
  {FVector(1750.f,1550.f,90.f), ENyResourceKind::EchoShard, 3},
  {FVector(2020.f,1550.f,90.f), ENyResourceKind::Berries, 5},
  {FVector(-2050.f,900.f,95.f), ENyResourceKind::Stone, 7},
  {FVector(-1810.f,1120.f,95.f), ENyResourceKind::Wood, 7},
  {FVector(450.f,-2350.f,90.f), ENyResourceKind::EchoShard, 6},
  {FVector(720.f,-2350.f,90.f), ENyResourceKind::EchoShard, 3},
  // Four guaranteed renewable water caches near the starting territory.
  {FVector(480.f,380.f,65.f), ENyResourceKind::Water, 8},
  {FVector(-480.f,380.f,65.f), ENyResourceKind::Water, 8},
  {FVector(-480.f,-380.f,65.f), ENyResourceKind::Water, 8},
  {FVector(480.f,-380.f,65.f), ENyResourceKind::Water, 8},
  {FVector(1950.f,1350.f,65.f), ENyResourceKind::Water, 8},
  {FVector(-2300.f,1150.f,65.f), ENyResourceKind::Water, 8}
 };
 for(const FSiteDrop& Drop : Drops){
  if(ANyResource* Node=W->SpawnActor<ANyResource>(NyServerGround(W,Drop.Position,Drop.Position.Z),FRotator::ZeroRotator)){
   Node->Setup(Drop.Kind,Drop.Amount);
  }
 }
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA Alpha 0.9] spawned %d POI resource nodes"), UE_ARRAY_COUNT(Drops));
}

// Shared server-authoritative loot with synchronized empty/refilled state.
void ANyGameMode::SpawnSiteLoot(){
 UWorld* W=GetWorld();if(!HasAuthority()||!W)return;
 struct FLocationLoot { FVector Position; ENyItemId Item; int32 Quantity; float Respawn; };
 const FLocationLoot Spots[]={
  {FVector(1510.f,1550.f,72.f),ENyItemId::EchoShard,2,240.f},
  {FVector(-2280.f,1100.f,72.f),ENyItemId::Stone,12,150.f},
  {FVector(-1910.f,780.f,72.f),ENyItemId::Wood,10,150.f},
  {FVector(650.f,-2490.f,72.f),ENyItemId::EchoShard,5,360.f}
 };
 for(const FLocationLoot& Spot:Spots){
  if(ANyLootCrate* Crate=W->SpawnActor<ANyLootCrate>(NyServerGround(W,Spot.Position,Spot.Position.Z),FRotator::ZeroRotator))
   Crate->Configure(Spot.Item,Spot.Quantity,Spot.Respawn);
 }
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA Alpha 0.10] %d shared loot crates spawned"),UE_ARRAY_COUNT(Spots));
}

void ANyGameMode::SpawnEnemies(){
 if(!HasAuthority()||!GetWorld())return;
 const FVector Positions[]={FVector(1150.f,1100.f,160.f),FVector(-1470.f,900.f,160.f),FVector(900.f,-1900.f,160.f),FVector(-900.f,-1100.f,160.f)};
 for(const FVector& P:Positions){
  FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
  GetWorld()->SpawnActor<ANyEnemy>(ANyEnemy::StaticClass(),NyServerGround(GetWorld(),P,P.Z),FRotator::ZeroRotator,Params);
 }
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA Alpha 0.12] %d prototype PvE enemies spawned"),UE_ARRAY_COUNT(Positions));
}


// Alpha 0.60 world persistence. UGameplayStatics writes to Saved/SaveGames.
// Never share these server-side files with clients, and back them up separately.
bool ANyGameMode::ShouldPersistBases() const{
 const UWorld* W=GetWorld();
 if(!HasAuthority()||!W||W->GetNetMode()==NM_Client)return false;
#if WITH_EDITOR
 // PIE uses multiple worlds and ephemeral player identities. Disable
 // disk persistence there to prevent tests from overwriting real world data.
 if(W->WorldType==EWorldType::PIE)return false;
#endif
 return true;
}

FString ANyGameMode::BaseSlotName() const{
 const FString Map=UGameplayStatics::GetCurrentLevelName(this,true);
 return Map.IsEmpty()?FString():TEXT("NYVERRA_Bases_v1_")+Map;
}

void ANyGameMode::RequestBaseSave(){
 if(!ShouldPersistBases()||bLoadingBases||bBaseSaveReadOnly)return;
 // Coalesce consecutive attacks and repairs, reducing disk activity.
 if(!GetWorldTimerManager().IsTimerActive(BaseDirtySaveTimer))
  GetWorldTimerManager().SetTimer(BaseDirtySaveTimer,this,
   &ANyGameMode::SaveBases,3.f,false);
}

void ANyGameMode::SaveBases(){
 if(!ShouldPersistBases()||bLoadingBases||bBaseSaveReadOnly)return;
 const FString Slot=BaseSlotName();
 if(Slot.IsEmpty())return;
 UWorld* W=GetWorld();
 if(!W)return;
 UNyBaseSaveGame* Save=Cast<UNyBaseSaveGame>(
  UGameplayStatics::CreateSaveGameObject(UNyBaseSaveGame::StaticClass()));
 if(!Save)return;
 Save->FormatVersion=1;
 Save->MapName=UGameplayStatics::GetCurrentLevelName(this,true);
 TSet<FGuid> Seen;
 for(TActorIterator<ANyBuildPiece> It(W);It;++It){
  ANyBuildPiece* Piece=*It;
  if(!IsValid(Piece)||Piece->Durability<=0.f)continue;
  if(!Piece->PersistentId.IsValid()){
   UE_LOG(LogTemp,Warning,TEXT("[NYVERRA BaseSave] Ignoring building with no persistent GUID"));
   continue;
  }
  if(Seen.Contains(Piece->PersistentId)) {
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Duplicate GUID; refusing to overwrite save"));
   return;
  }
  Seen.Add(Piece->PersistentId);
  if(Save->Pieces.Num()>=1024){
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] 1024-piece cap exceeded; save untouched"));
   return;
  }
  FNySavedBuildPiece& Entry=Save->Pieces.AddDefaulted_GetRef();
  Entry.PersistentId=Piece->PersistentId;
  Entry.PieceType=Piece->PieceType;
  Entry.Location=Piece->GetActorLocation();
  Entry.Rotation=Piece->GetActorRotation();
  Entry.Durability=Piece->Durability;
  Entry.OwnerNetworkId=Piece->BuilderNetworkId;
 }
 if(!UGameplayStatics::SaveGameToSlot(Save,Slot,0))
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] FAILED writing %s; check disk permissions"),*Slot);
 else
  UE_LOG(LogTemp,Display,TEXT("[NYVERRA BaseSave] Saved %d pieces to %s"),Save->Pieces.Num(),*Slot);
}

void ANyGameMode::LoadBases(){
 if(!ShouldPersistBases())return;
 const FString Slot=BaseSlotName();
 if(Slot.IsEmpty()||!UGameplayStatics::DoesSaveGameExist(Slot,0))return;
 UNyBaseSaveGame* Save=Cast<UNyBaseSaveGame>(
  UGameplayStatics::LoadGameFromSlot(Slot,0));
 const FString CurrentMap=UGameplayStatics::GetCurrentLevelName(this,true);
 if(!Save||Save->FormatVersion!=1||Save->MapName!=CurrentMap||
    Save->Pieces.Num()>1024){
  bBaseSaveReadOnly=true; // Protect unknown, incompatible or damaged saves.
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Invalid save; read-only until admin backup/repair"));
  return;
 }
 // Validate the complete input BEFORE spawning any actors. A malformed save
 // must never erase, duplicate or partially replace the world.
 TSet<FGuid> Seen;
 for(const FNySavedBuildPiece& E:Save->Pieces){
  const float ExpectedHP=E.PieceType==0?600.f:E.PieceType==1?360.f:280.f;
  const bool bBad=E.PieceType>2||!E.PersistentId.IsValid()||
   E.Location.ContainsNaN()||E.Rotation.ContainsNaN()||
   FMath::Abs(E.Location.X)>5000.f||FMath::Abs(E.Location.Y)>5000.f||
   FMath::Abs(E.Location.Z)>10000.f||!FMath::IsFinite(E.Durability)||
   E.Durability<=0.f||E.Durability>ExpectedHP||
   E.OwnerNetworkId.Len()>256||Seen.Contains(E.PersistentId);
  if(bBad){
   bBaseSaveReadOnly=true;
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Invalid building record; no actors loaded"));
   return;
  }
  Seen.Add(E.PersistentId);
 }
 bLoadingBases=true;
 int32 Restored=0;
 for(const FNySavedBuildPiece& E:Save->Pieces){
  FActorSpawnParameters Params;
  Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  ANyBuildPiece* Piece=GetWorld()->SpawnActor<ANyBuildPiece>(
   ANyBuildPiece::StaticClass(),E.Location,E.Rotation,Params);
  if(!Piece){
   bBaseSaveReadOnly=true; // Never overwrite a save after a partial load.
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Could not spawn saved building; slot read-only"));
   break;
  }
  Piece->RestoreFromSave(E.PieceType,E.PersistentId,E.Durability,E.OwnerNetworkId);
  ++Restored;
 }
 bLoadingBases=false;
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA BaseSave] Loaded %d / %d pieces from %s"),
  Restored,Save->Pieces.Num(),*Slot);
}

void ANyGameMode::BindPlayerToSavedBases(APlayerState* Player){
 if(!HasAuthority()||!IsValid(Player))return;
 // For online identities only. No name-based recovery or unverified RPC
 // is allowed to take over someone else's locked door.
 for(TActorIterator<ANyBuildPiece> It(GetWorld());It;++It)
  if(IsValid(*It))It->BindReturningOwner(Player);
}

void ANyGameMode::PostLogin(APlayerController* NewPlayer){
 Super::PostLogin(NewPlayer);
 if(NewPlayer)BindPlayerToSavedBases(NewPlayer->GetPlayerState<APlayerState>());
}

void ANyGameMode::Logout(AController* Exiting){
 APlayerState* Departing=Exiting?Exiting->GetPlayerState<APlayerState>():nullptr;
 if(HasAuthority()&&IsValid(Departing)){
  for(TActorIterator<ANyBuildPiece> It(GetWorld());It;++It)
   if(IsValid(*It))It->UnbindDepartingOwner(Departing);
 }
 Super::Logout(Exiting);
}
