#include "NyGameMode.h"
#include "NyCharacter.h"
#include "NyResource.h"
#include "NyLootCrate.h"
#include "NyEnemy.h"
#include "NyHUD.h"
#include "NyWorldState.h"
#include "NyBuildPiece.h"
#include "NyBaseSaveGame.h"
#include "NyPlayerSaveGame.h"
#include "Misc/SecureHash.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
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
  if(ShouldPersistPlayers())
   GetWorldTimerManager().SetTimer(PlayerAutosaveTimer,this,
    &ANyGameMode::SaveActivePlayers,60.f,true);
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
 const FString PrimarySlot=BaseSlotName();
 if(PrimarySlot.IsEmpty()||BaseSaveRevision==MAX_int64)return;
 const FString TargetSlot=bNextSaveToBackup?
  PrimarySlot+TEXT("_B"):PrimarySlot;
 UWorld* W=GetWorld();
 if(!W)return;
 UNyBaseSaveGame* Save=Cast<UNyBaseSaveGame>(
  UGameplayStatics::CreateSaveGameObject(UNyBaseSaveGame::StaticClass()));
 if(!Save)return;
 Save->FormatVersion=1;
 Save->SaveRevision=BaseSaveRevision+1;
 Save->MapName=UGameplayStatics::GetCurrentLevelName(this,true);
 TSet<FGuid> Seen;
 for(TActorIterator<ANyBuildPiece> It(W);It;++It){
  ANyBuildPiece* Piece=*It;
  if(!IsValid(Piece)||Piece->Durability<=0.f)continue;
  if(!Piece->PersistentId.IsValid()){
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Building missing GUID; save untouched"));
   return;
  }
  const FVector Position=Piece->GetActorLocation();
  const FRotator Facing=Piece->GetActorRotation();
  const float Maximum=Piece->PieceType==0?600.f:Piece->PieceType==1?360.f:280.f;
  if(Piece->PieceType>2||Position.ContainsNaN()||Facing.ContainsNaN()||
     FMath::Abs(Position.X)>5000.f||FMath::Abs(Position.Y)>5000.f||
     FMath::Abs(Position.Z)>10000.f||
     !FMath::IsFinite(Piece->Durability)||Piece->Durability>Maximum||
     Piece->BuilderNetworkId.Len()>256){
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Invalid live building; save untouched"));
   return;
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
 if(!UGameplayStatics::SaveGameToSlot(Save,TargetSlot,0)){
  bBaseSaveReadOnly=true; // Disk failure: block changes which cannot be persisted.
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] FAILED writing %s; world locked read-only"),*TargetSlot);
  return;
 }
 // A reported successful write must be readable before we advance the
 // generation. If verification fails, the other slot remains intact.
 UNyBaseSaveGame* Verified=Cast<UNyBaseSaveGame>(
  UGameplayStatics::LoadGameFromSlot(TargetSlot,0));
 if(!Verified||Verified->FormatVersion!=1||
    Verified->SaveRevision!=Save->SaveRevision||
    Verified->MapName!=Save->MapName||
    Verified->Pieces.Num()!=Save->Pieces.Num()){
  bBaseSaveReadOnly=true;
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Read-back verification failed for %s; world locked read-only"),*TargetSlot);
  return;
 }
 // Compare each saved record, not just the header and array length.
 // This catches a readable but partially modified/truncated snapshot.
 for(int32 Index=0;Index<Save->Pieces.Num();++Index){
  const FNySavedBuildPiece& Original=Save->Pieces[Index];
  const FNySavedBuildPiece& Disk=Verified->Pieces[Index];
  if(Original.PersistentId!=Disk.PersistentId||
     Original.PieceType!=Disk.PieceType||
     !Original.Location.Equals(Disk.Location,KINDA_SMALL_NUMBER)||
     !Original.Rotation.Equals(Disk.Rotation,KINDA_SMALL_NUMBER)||
     !FMath::IsNearlyEqual(Original.Durability,Disk.Durability)||
     Original.OwnerNetworkId!=Disk.OwnerNetworkId){
   bBaseSaveReadOnly=true;
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Record mismatch after read-back; world locked read-only"));
   return;
  }
 }
 BaseSaveRevision=Save->SaveRevision;
 bNextSaveToBackup=!bNextSaveToBackup;
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA BaseSave] Revision %lld: saved %d pieces to %s"),
  static_cast<long long>(BaseSaveRevision),Save->Pieces.Num(),*TargetSlot);
}

void ANyGameMode::LoadBases(){
 if(!ShouldPersistBases())return;
 const FString SlotA=BaseSlotName();
 if(SlotA.IsEmpty())return;
 const FString SlotB=SlotA+TEXT("_B");
 const bool bHaveA=UGameplayStatics::DoesSaveGameExist(SlotA,0);
 const bool bHaveB=UGameplayStatics::DoesSaveGameExist(SlotB,0);
 if(!bHaveA&&!bHaveB)return;

 // Validate BOTH slots independently. A failed/incomplete write to one slot
 // must never destroy the older valid snapshot on the other slot.
 const FString CurrentMap=UGameplayStatics::GetCurrentLevelName(this,true);
 auto IsValidSnapshot=[&CurrentMap](const UNyBaseSaveGame* Snapshot)->bool{
  if(!Snapshot||Snapshot->FormatVersion!=1||
     Snapshot->SaveRevision<0||Snapshot->SaveRevision==MAX_int64||
     Snapshot->MapName!=CurrentMap||Snapshot->Pieces.Num()>1024)return false;
  TSet<FGuid> Seen;
  for(const FNySavedBuildPiece& E:Snapshot->Pieces){
   const float ExpectedHP=E.PieceType==0?600.f:E.PieceType==1?360.f:280.f;
   if(E.PieceType>2||!E.PersistentId.IsValid()||
      E.Location.ContainsNaN()||E.Rotation.ContainsNaN()||
      FMath::Abs(E.Location.X)>5000.f||FMath::Abs(E.Location.Y)>5000.f||
      FMath::Abs(E.Location.Z)>10000.f||!FMath::IsFinite(E.Durability)||
      E.Durability<=0.f||E.Durability>ExpectedHP||
      E.OwnerNetworkId.Len()>256||Seen.Contains(E.PersistentId))return false;
   Seen.Add(E.PersistentId);
  }
  return true;
 };
 UNyBaseSaveGame* SaveA=bHaveA?Cast<UNyBaseSaveGame>(
  UGameplayStatics::LoadGameFromSlot(SlotA,0)):nullptr;
 UNyBaseSaveGame* SaveB=bHaveB?Cast<UNyBaseSaveGame>(
  UGameplayStatics::LoadGameFromSlot(SlotB,0)):nullptr;
 const bool bValidA=bHaveA&&IsValidSnapshot(SaveA);
 const bool bValidB=bHaveB&&IsValidSnapshot(SaveB);
 if(!bValidA&&!bValidB){
  bBaseSaveReadOnly=true; // Never overwrite the only copies of broken data.
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Both snapshots invalid; read-only until backup/repair"));
  return;
 }
 // Legacy Alpha 0.60 single-slot SaveGame has SaveRevision=0 and loads as A.
 const bool bUseB=bValidB&&(!bValidA||SaveB->SaveRevision>SaveA->SaveRevision);
 UNyBaseSaveGame* Save=bUseB?SaveB:SaveA;
 BaseSaveRevision=Save->SaveRevision;
 // Next write goes to the OTHER slot, never overwriting the just-loaded copy.
 bNextSaveToBackup=!bUseB;
 if((bHaveA&&!bValidA)||(bHaveB&&!bValidB))
  UE_LOG(LogTemp,Warning,TEXT("[NYVERRA BaseSave] Invalid snapshot ignored; recovered from valid %s"),bUseB?TEXT("B"):TEXT("A"));
 bLoadingBases=true;
 int32 Restored=0;
 for(const FNySavedBuildPiece& E:Save->Pieces){
  FActorSpawnParameters Params;
  Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
  ANyBuildPiece* Piece=GetWorld()->SpawnActor<ANyBuildPiece>(
   ANyBuildPiece::StaticClass(),E.Location,E.Rotation,Params);
  if(!Piece){
   bBaseSaveReadOnly=true; // Do not write an incomplete world over either slot.
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA BaseSave] Spawn failed; protected read-only state"));
   break;
  }
  Piece->RestoreFromSave(E.PieceType,E.PersistentId,E.Durability,E.OwnerNetworkId);
  ++Restored;
 }
 bLoadingBases=false;
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA BaseSave] Loaded %d/%d pieces, revision %lld, slot %s"),
  Restored,Save->Pieces.Num(),static_cast<long long>(BaseSaveRevision),
  bUseB?TEXT("B"):TEXT("A"));
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
 // Save before Super::Logout destroys PlayerState/pawn ownership.
 if(Exiting){
  if(ANyCharacter* Pawn=Cast<ANyCharacter>(Exiting->GetPawn()))
   SavePlayerState(Pawn);
  PlayerLoadAttemptedControllers.Remove(Exiting);
 }
 APlayerState* Departing=Exiting?Exiting->GetPlayerState<APlayerState>():nullptr;
 if(HasAuthority()&&IsValid(Departing)){
  for(TActorIterator<ANyBuildPiece> It(GetWorld());It;++It)
   if(IsValid(*It))It->UnbindDepartingOwner(Departing);
 }
 Super::Logout(Exiting);
}


// Alpha 0.62 — player inventories / survival stats use separate server slots.
// NO online persistence by default. A dedicated/listen server must configure
// genuine, authenticated OnlineSubsystem IDs and explicitly opt in with
// -NyAllowAuthenticatedPlayerSaves. Null/LAN IDs are not secure credentials.
bool ANyGameMode::ShouldPersistPlayers() const{
 return ShouldPersistBases();
}

FString ANyGameMode::PlayerPersistenceKey(const APlayerState* Player) const{
 if(!ShouldPersistPlayers()||!IsValid(Player)||!GetWorld())return FString();
 if(GetWorld()->GetNetMode()!=NM_Standalone &&
    !FParse::Param(FCommandLine::Get(),TEXT("NyAllowAuthenticatedPlayerSaves")))
  return FString(); // A valid ID is not proof of online authentication.
 return ANyBuildPiece::OnlineOwnerKey(Player);
}

FString ANyGameMode::PlayerSaveSlot(const FString& Key) const{
 const FString Map=UGameplayStatics::GetCurrentLevelName(this,true);
 if(Key.IsEmpty()||Map.IsEmpty())return FString();
 // Hashing avoids treating provider-specific account IDs as file paths.
 // This digest is an INDEX, not authentication or encryption.
 return TEXT("NYVERRA_Player_v1_")+FMD5::HashAnsiString(*(Map+TEXT("|")+Key));
}

bool ANyGameMode::HasDuplicatePlayerIdentity(const ANyCharacter* Pawn,
                                               const FString& Key) const{
 if(Key.IsEmpty()||!GetWorld())return false;
 for(FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator();It;++It){
  const APlayerController* Other=It->Get();
  if(!IsValid(Other)||Other->GetPawn()==Pawn)continue;
  if(PlayerPersistenceKey(Other->GetPlayerState<APlayerState>())==Key)return true;
 }
 return false;
}

void ANyGameMode::CheckpointPlayerDeath(ANyCharacter* Player){
 // Server-authoritative death should be durable before the eight-second
 // respawn. SavePlayerState captures a tombstone with NO inventory contents.
 // Failed/unsafe writes are protected by the existing A/B slot guard.
 if(!HasAuthority()||!IsValid(Player)||!Player->HasAuthority()||
    !Player->bIsDead||Player->Health>0.f)return;
 SavePlayerState(Player);
}

void ANyGameMode::RequestPlayerSave(){
 if(!ShouldPersistPlayers()||bLoadingPlayerState)return;
 // Multiple inventory operations / survival ticks share one disk write.
 if(!GetWorldTimerManager().IsTimerActive(PlayerDirtySaveTimer))
  GetWorldTimerManager().SetTimer(PlayerDirtySaveTimer,this,
   &ANyGameMode::SaveActivePlayers,20.f,false);
}

// Strict validation BEFORE applying server state or trusting a snapshot.
static bool NyValidPlayerSnapshot(const UNyPlayerSaveGame* Save,
                                  const FString& Map,const FString& Digest){
 if(!Save||Save->FormatVersion!=1||Save->SaveRevision<0||
    Save->SaveRevision==MAX_int64||Save->MapName!=Map||
    Save->OwnerDigest!=Digest||Save->Inventory.Num()>16||
    Save->DeathCount<0||Save->DeathCount>1000000)return false;
 const float Values[]={Save->Health,Save->Hunger,Save->Thirst,Save->Stamina};
 for(float Value:Values)if(!FMath::IsFinite(Value)||Value<0.f||Value>100.f)return false;
 // A death checkpoint must have zero HP and no inventory. Otherwise a
 // corrupted newer save could resurrect lost loot after reconnecting.
 if((!Save->bWasDead&&Save->Health<=0.f)||
    (Save->bWasDead&&(Save->Health>0.f||Save->Inventory.Num()>0)))return false;
 for(const FNySavedPlayerStack& Entry:Save->Inventory){
  if(Entry.ItemId>static_cast<uint8>(ENyItemId::Bandage))return false;
  const bool bTool=Entry.ItemId==static_cast<uint8>(ENyItemId::Axe)||
                   Entry.ItemId==static_cast<uint8>(ENyItemId::Pickaxe);
  if(Entry.Quantity<=0||Entry.Quantity>(bTool?1:100))return false;
 }
 return true;
}

void ANyGameMode::LoadPlayerState(ANyCharacter* Pawn){
 if(!ShouldPersistPlayers()||!IsValid(Pawn)||!Pawn->HasAuthority())return;
 const FString Key=PlayerPersistenceKey(Pawn->GetPlayerState());
 const FString SlotA=PlayerSaveSlot(Key);
 if(SlotA.IsEmpty())return;
 if(HasDuplicatePlayerIdentity(Pawn,Key)){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Concurrent owner identity: persistence disabled until restart"));
  return;
 }
 const FString SlotB=SlotA+TEXT("_B");
 const bool HasA=UGameplayStatics::DoesSaveGameExist(SlotA,0);
 const bool HasB=UGameplayStatics::DoesSaveGameExist(SlotB,0);
 if(!HasA&&!HasB)return;
 const FString Map=UGameplayStatics::GetCurrentLevelName(this,true);
 const FString Digest=FMD5::HashAnsiString(*Key);
 UNyPlayerSaveGame* A=HasA?Cast<UNyPlayerSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotA,0)):nullptr;
 UNyPlayerSaveGame* B=HasB?Cast<UNyPlayerSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotB,0)):nullptr;
 const bool ValidA=HasA&&NyValidPlayerSnapshot(A,Map,Digest);
 const bool ValidB=HasB&&NyValidPlayerSnapshot(B,Map,Digest);
 if(!ValidA&&!ValidB){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Both player snapshots invalid; refusing to overwrite %s"),*SlotA);
  return;
 }
 const bool UseB=ValidB&&(!ValidA||B->SaveRevision>A->SaveRevision);
 UNyPlayerSaveGame* Best=UseB?B:A;
 PlayerSaveRevisions.Add(SlotA,Best->SaveRevision);
 PlayerNextBackup.Add(SlotA,!UseB);
 bLoadingPlayerState=true;
 const bool Loaded=Pawn->ApplyPersistentState(Best);
 bLoadingPlayerState=false;
 if(!Loaded){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Could not apply validated player state; slot protected"));
  return;
 }
 if((HasA&&!ValidA)||(HasB&&!ValidB))
  UE_LOG(LogTemp,Warning,TEXT("[NYVERRA PlayerSave] Recovered from valid %s snapshot"),UseB?TEXT("B"):TEXT("A"));
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA PlayerSave] Restored revision %lld from slot %s"),
  static_cast<long long>(Best->SaveRevision),UseB?TEXT("B"):TEXT("A"));
}

void ANyGameMode::SavePlayerState(ANyCharacter* Pawn){
 if(!ShouldPersistPlayers()||bLoadingPlayerState||!IsValid(Pawn)||!Pawn->HasAuthority())return;
 const FString Key=PlayerPersistenceKey(Pawn->GetPlayerState());
 const FString SlotA=PlayerSaveSlot(Key);
 if(SlotA.IsEmpty()||ProtectedPlayerSlots.Contains(SlotA))return;
 if(HasDuplicatePlayerIdentity(Pawn,Key)){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Duplicate session detected; refusing snapshot write"));
  return;
 }
 const int64 Revision=PlayerSaveRevisions.FindRef(SlotA);
 if(Revision==MAX_int64)return;
 const bool UseB=PlayerNextBackup.FindRef(SlotA);
 const FString Target=UseB?SlotA+TEXT("_B"):SlotA;
 UNyPlayerSaveGame* Save=Cast<UNyPlayerSaveGame>(
  UGameplayStatics::CreateSaveGameObject(UNyPlayerSaveGame::StaticClass()));
 if(!Save||!Pawn->CapturePersistentState(Save)){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Invalid live state; player save locked"));
  return;
 }
 Save->FormatVersion=1;
 Save->SaveRevision=Revision+1;
 Save->MapName=UGameplayStatics::GetCurrentLevelName(this,true);
 Save->OwnerDigest=FMD5::HashAnsiString(*Key);
 if(!UGameplayStatics::SaveGameToSlot(Save,Target,0)){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Write failed; player save locked"));
  return;
 }
 UNyPlayerSaveGame* Disk=Cast<UNyPlayerSaveGame>(UGameplayStatics::LoadGameFromSlot(Target,0));
 if(!NyValidPlayerSnapshot(Disk,Save->MapName,Save->OwnerDigest)||
    Disk->SaveRevision!=Save->SaveRevision||
    Disk->Inventory.Num()!=Save->Inventory.Num()||
    Disk->DeathCount!=Save->DeathCount||
    Disk->bWasDead!=Save->bWasDead||
    !FMath::IsNearlyEqual(Disk->Health,Save->Health)||
    !FMath::IsNearlyEqual(Disk->Hunger,Save->Hunger)||
    !FMath::IsNearlyEqual(Disk->Thirst,Save->Thirst)||
    !FMath::IsNearlyEqual(Disk->Stamina,Save->Stamina)){
  ProtectedPlayerSlots.Add(SlotA);
  UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Read-back validation failed; player save locked"));
  return;
 }
 for(int32 i=0;i<Save->Inventory.Num();++i){
  if(Disk->Inventory[i].ItemId!=Save->Inventory[i].ItemId||
     Disk->Inventory[i].Quantity!=Save->Inventory[i].Quantity){
   ProtectedPlayerSlots.Add(SlotA);
   UE_LOG(LogTemp,Error,TEXT("[NYVERRA PlayerSave] Read-back inventory mismatch; slot protected"));
   return;
  }
 }
 PlayerSaveRevisions.Add(SlotA,Save->SaveRevision);
 PlayerNextBackup.Add(SlotA,!UseB);
 UE_LOG(LogTemp,Verbose,TEXT("[NYVERRA PlayerSave] Saved revision %lld"),
  static_cast<long long>(Save->SaveRevision));
}

void ANyGameMode::SaveActivePlayers(){
 if(!ShouldPersistPlayers()||!GetWorld())return;
 for(FConstPlayerControllerIterator It=GetWorld()->GetPlayerControllerIterator();It;++It){
  APlayerController* PC=It->Get();
  if(!IsValid(PC))continue;
  if(ANyCharacter* Pawn=Cast<ANyCharacter>(PC->GetPawn()))
   SavePlayerState(Pawn);
 }
}

void ANyGameMode::RestartPlayer(AController* NewPlayer){
 Super::RestartPlayer(NewPlayer);
 if(!HasAuthority()||!NewPlayer||PlayerLoadAttemptedControllers.Contains(NewPlayer))return;
 ANyCharacter* Pawn=Cast<ANyCharacter>(NewPlayer->GetPawn());
 if(!IsValid(Pawn))return;
 // Only first spawn per connected controller may load a disk snapshot.
 // A later respawn must not resurrect older inventory and undo death loss.
 PlayerLoadAttemptedControllers.Add(NewPlayer);
 LoadPlayerState(Pawn);
}

void ANyGameMode::EndPlay(const EEndPlayReason::Type EndPlayReason){
 if(HasAuthority()&&ShouldPersistPlayers())SaveActivePlayers();
 PlayerLoadAttemptedControllers.Reset();
 Super::EndPlay(EndPlayReason);
}
