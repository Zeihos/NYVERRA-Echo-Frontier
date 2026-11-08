#include "NyGameMode.h"
#include "NyCharacter.h"
#include "NyResource.h"
#include "NyLootCrate.h"
#include "NyEnemy.h"
#include "NyHUD.h"
#include "NyWorldState.h"
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
  SpawnServerResources(); SpawnSiteResources(); SpawnSiteLoot(); SpawnEnemies(); }
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
