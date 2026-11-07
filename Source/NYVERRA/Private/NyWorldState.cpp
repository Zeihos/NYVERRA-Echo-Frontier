#include "NyWorldState.h"
#include "Net/UnrealNetwork.h"
#include "Engine/World.h"
#include "Engine/EngineTypes.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "EngineUtils.h"
#include "UObject/UObjectGlobals.h"

ANyWorldState::ANyWorldState(){ bReplicates=true; PrimaryActorTick.bCanEverTick=true; }
void ANyWorldState::BeginPlay(){
 Super::BeginPlay();
 // Identical collision ground exists on dedicated server and every client.
 // Environment decoration is client-local and must not affect gameplay collision.
 // The authored TestWorld floor is baked into the navigation mesh.
 // Runtime ground is retained for Entry or other legacy test maps only.
 if (!GetWorld()->GetMapName().Contains(TEXT("TestWorld")) && !GetWorld()->GetMapName().Contains(TEXT("TestLandscape"))) { CreateCollisionGround(); }
 CreateExplorationSites();
 if(GetNetMode()!=NM_DedicatedServer){ GenerateLocalTerrain(); CreateAtmosphere(); }
}
void ANyWorldState::Tick(float DT){
 Super::Tick(DT);
 if(HasAuthority()){
  TimeOfDayHours=FMath::Fmod(TimeOfDayHours + DT/180.f,24.f);
  Accumulator+=DT;
  while(Accumulator>=1.f){Accumulator-=1.f;--EchoSeconds;
   if(EchoSeconds<=0){bEchoActive=!bEchoActive;EchoSeconds=bEchoActive?35:90;ForceNetUpdate();}
   --WeatherSeconds;
   if(WeatherSeconds<=0){bRainActive=!bRainActive;WeatherSeconds=bRainActive?90:160;ForceNetUpdate();}
  }
 }
 if(GetNetMode()!=NM_DedicatedServer){
  VisualUpdateAccumulator+=DT;
  if(VisualUpdateAccumulator>=0.25f || bLastEcho!=bEchoActive){VisualUpdateAccumulator=0.f;UpdateAtmosphere();}
 }
}
void ANyWorldState::CreateCollisionGround(){
 UWorld* W=GetWorld(); if(!W)return;
 UStaticMesh* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
 if(!Cube)return;
 AStaticMeshActor* Ground=W->SpawnActor<AStaticMeshActor>(FVector(0,0,-115),FRotator::ZeroRotator);
 if(!Ground)return;
 Ground->SetReplicates(false); // Created locally on server and clients at identical coordinates.
 UStaticMeshComponent* Mesh=Ground->GetStaticMeshComponent();
 // A runtime ground is a fixed terrain surface; a Movable root caused
 // authoritative construction to reject it (building requires Static ground).
 Mesh->SetMobility(EComponentMobility::Static);
 Mesh->SetStaticMesh(Cube);
 Mesh->SetCollisionProfileName(TEXT("BlockAll"));
 Ground->SetActorScale3D(FVector(85,85,2));
}

// Alpha 0.8: Server and clients instantiate the SAME three collision sites.
// Sites use built-in engine primitives, requiring no downloaded art and no replication.
// Gameplay items inside sites remain separate server-owned replicated actors.
void ANyWorldState::CreateExplorationSites(){
 UWorld* World=GetWorld(); if(!World)return;
 UStaticMesh* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
 UStaticMesh* Cylinder=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
 if(!Cube||!Cylinder)return;
 auto Place=[&](UStaticMesh* Shape,const FVector& Position,const FVector& Scale,const FRotator& Rotation){
  AStaticMeshActor* A=World->SpawnActor<AStaticMeshActor>(Position,Rotation);
  if(!A)return;
  A->SetReplicates(false);
  A->Tags.AddUnique(TEXT("NYVERRA_SiteGeometry"));
  UStaticMeshComponent* M=A->GetStaticMeshComponent();
  M->SetMobility(EComponentMobility::Movable);
  M->SetStaticMesh(Shape);
  M->SetCollisionProfileName(TEXT("BlockAll"));
  A->SetActorScale3D(Scale);
 };
 // Sample site elevations BEFORE any site meshes exist, preventing traces from hitting
 // our own platforms. This gives server and clients matching site positions on a saved map.
 auto SiteOrigin=[&](float X,float Y)->FVector{
  FHitResult Hit;
  FCollisionQueryParams Query(SCENE_QUERY_STAT(NySiteGround),false);
  const FVector Start(X,Y,50000.f), End(X,Y,-50000.f);
  if(World->LineTraceSingleByChannel(Hit,Start,End,ECC_Visibility,Query))
   return FVector(X,Y,Hit.ImpactPoint.Z);
  UE_LOG(LogTemp,Warning,TEXT("[NYVERRA 0.21] No blocking terrain at POI XY=(%.0f,%.0f); falling back to Z=0"),X,Y);
  return FVector(X,Y,0.f);
 };
 const FVector Relay=SiteOrigin(1750.f,1550.f);
 const FVector Depot=SiteOrigin(-2050.f,900.f);
 const FVector EchoSite=SiteOrigin(450.f,-2350.f);
 // Point of interest 1: radio relay with an accessible courtyard to the east.
 Place(Cube,Relay+FVector(0,0,15),FVector(9,8,.3),FRotator::ZeroRotator);
 for(int32 i=0;i<4;++i){
  const float X=(i<2?-400.f:400.f);
  const float Y=(i%2==0?-330.f:330.f);
  Place(Cylinder,Relay+FVector(X,Y,180.f),FVector(.42f,.42f,3.6f),FRotator::ZeroRotator);
 }
 Place(Cube,Relay+FVector(0,-350,300),FVector(8,.55f,.35f),FRotator::ZeroRotator);
 Place(Cube,Relay+FVector(0,350,300),FVector(8,.55f,.35f),FRotator::ZeroRotator);
 Place(Cube,Relay+FVector(-410,0,300),FVector(.55f,7,.35f),FRotator::ZeroRotator);
 Place(Cylinder,Relay+FVector(0,0,360),FVector(.7f,.7f,7.2f),FRotator::ZeroRotator);
 // Point of interest 2: broken logistics depot, with a deliberate door gap.
 Place(Cube,Depot+FVector(0,0,12),FVector(11,9,.24),FRotator::ZeroRotator);
 Place(Cube,Depot+FVector(0,-450,180),FVector(11,.35f,3.6f),FRotator::ZeroRotator);
 Place(Cube,Depot+FVector(-550,0,180),FVector(.35f,9,3.6f),FRotator::ZeroRotator);
 Place(Cube,Depot+FVector(550,-260,180),FVector(.35f,3.8f,3.6f),FRotator::ZeroRotator);
 Place(Cube,Depot+FVector(550,310,180),FVector(.35f,2.8f,3.6f),FRotator::ZeroRotator);
 for(int32 i=0;i<5;++i){
  Place(Cube,Depot+FVector(-350.f+170.f*i,110.f+(i%2)*130.f,60.f),FVector(1.1f,1.1f,1.2f),FRotator(0.f,i*14.f,0.f));
 }
 // Point of interest 3: an echo research circle, visually identifiable from distance.
 Place(Cube,EchoSite+FVector(0,0,10),FVector(8,8,.2),FRotator(0,30,0));
 for(int32 i=0;i<8;++i){
  const float Angle=i*2.f*PI/8.f;
  Place(Cylinder,EchoSite+FVector(FMath::Cos(Angle)*480.f,FMath::Sin(Angle)*480.f,125.f),FVector(.45f,.45f,2.5f),FRotator::ZeroRotator);
 }
 Place(Cylinder,EchoSite+FVector(0,0,225),FVector(1.3f,1.3f,4.5f),FRotator::ZeroRotator);
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA 0.21] POIs elevated: relay=%.1f depot=%.1f echo=%.1f"),Relay.Z,Depot.Z,EchoSite.Z);
}

// Alpha 0.20: Align non-colliding decoration to actual terrain collision.
// If no terrain is present, fall back to the legacy flat prototype surface.
static FVector NyDecorGround(UWorld* World, const FVector& XY, float HeightOffset)
{
 FHitResult Hit;
 const FVector Start(XY.X,XY.Y,50000.f);
 const FVector End(XY.X,XY.Y,-50000.f);
 FCollisionQueryParams Query(SCENE_QUERY_STAT(NyDecorGround),false);
 if(World && World->LineTraceSingleByChannel(Hit,Start,End,ECC_Visibility,Query))
  return FVector(XY.X,XY.Y,Hit.ImpactPoint.Z+HeightOffset);
 return FVector(XY.X,XY.Y,HeightOffset-15.f);
}
void ANyWorldState::GenerateLocalTerrain(){
 UWorld* W=GetWorld();if(!W)return;
 UStaticMesh* Cube=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
 UStaticMesh* Cylinder=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
 UStaticMesh* Sphere=LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere"));
 if(!Cube||!Cylinder||!Sphere)return;
 auto MakeInstances=[&](const TCHAR* Name,UStaticMesh* Shape)->UHierarchicalInstancedStaticMeshComponent*{
  UHierarchicalInstancedStaticMeshComponent* H=NewObject<UHierarchicalInstancedStaticMeshComponent>(this,Name);
  if(!H)return nullptr;
  H->SetStaticMesh(Shape);
  H->SetCollisionEnabled(ECollisionEnabled::NoCollision); // decor doesn't affect server authority
  H->SetMobility(EComponentMobility::Movable);
  H->RegisterComponent();
  return H;
 };
 Trunks=MakeInstances(TEXT("ForestTrunks"),Cylinder);
 Canopies=MakeInstances(TEXT("ForestCanopies"),Sphere);
 Rocks=MakeInstances(TEXT("ScatterRocks"),Sphere);
 // Alpha 0.18: separate instanced silhouettes make the three biomes readable.
 UHierarchicalInstancedStaticMeshComponent* Ridge=MakeInstances(TEXT("DistantRidges"),Cube);
 FRandomStream RNG(190731);
 for(int32 i=0;i<360;i++){
  const FVector XY(RNG.FRandRange(-3950,3950),RNG.FRandRange(-3950,3950),0.f);
  const FVector P=NyDecorGround(W,XY,0.f);
  if(P.Size2D()<650)continue;
  // Clearings around shared POIs prevent decorative foliage from occluding sites.
  const FVector2D PlanarPoint(P.X,P.Y);
  if(FVector2D::Distance(PlanarPoint,FVector2D(1750.f,1550.f))<1150.f ||
     FVector2D::Distance(PlanarPoint,FVector2D(-2050.f,900.f))<1300.f ||
     FVector2D::Distance(PlanarPoint,FVector2D(450.f,-2350.f))<1050.f)continue;
  const float S=RNG.FRandRange(.7f,1.45f);
  const float Yaw=RNG.FRandRange(0,360);
  if(i%5!=0){
   if(Trunks)Trunks->AddInstance(FTransform(FRotator(0,Yaw,0),P+FVector(0,0,120*S),FVector(.18f*S,.18f*S,2.4f*S)));
   if(Canopies)Canopies->AddInstance(FTransform(FRotator(0,Yaw,0),P+FVector(0,0,250*S),FVector(1.1f*S,1.1f*S,1.8f*S)));
  }else if(Rocks){
   Rocks->AddInstance(FTransform(FRotator(0,Yaw,0),P+FVector(0,0,35*S),FVector(1.3f*S,.9f*S,.55f*S)));
  }
 }
 // Distant skyline: cosmetic, non-colliding ridges along the map border.
 // This is deliberately NOT a UE Landscape and does not alter authoritative collision.
 if(Ridge){
  FRandomStream RidgeRNG(180018);
  for(int32 i=0;i<76;++i){
   const float Angle=(2.f*PI*i)/76.f;
   const float Radius=RidgeRNG.FRandRange(3450.f,4050.f);
   const float Elevation=RidgeRNG.FRandRange(180.f,690.f);
   const FVector Pos(FMath::Cos(Angle)*Radius,FMath::Sin(Angle)*Radius,Elevation*.45f-70.f);
   Ridge->AddInstance(FTransform(FRotator(0.f,FMath::RadiansToDegrees(Angle),0.f),Pos,
     FVector(RidgeRNG.FRandRange(2.4f,5.8f),RidgeRNG.FRandRange(3.5f,7.5f),Elevation/100.f)));
  }
 }
 // A denser cold northern grove and sparse dry western scrub visually separate biomes.
 if(Trunks && Canopies){
  FRandomStream RegionRNG(180019);
  for(int32 i=0;i<115;++i){
   const bool bNorth=i<65;
   const FVector XY(bNorth?RegionRNG.FRandRange(250.f,3250.f):RegionRNG.FRandRange(-3550.f,-2200.f),
      bNorth?RegionRNG.FRandRange(2400.f,3650.f):RegionRNG.FRandRange(-2500.f,-850.f),0.f);
   const FVector P=NyDecorGround(W,XY,0.f);
   // Maintain clearings around the radio station, depot and Echo circle.
   if(FVector2D::Distance(FVector2D(P.X,P.Y),FVector2D(1750.f,1550.f))<1150.f ||
      FVector2D::Distance(FVector2D(P.X,P.Y),FVector2D(-2050.f,900.f))<1300.f ||
      FVector2D::Distance(FVector2D(P.X,P.Y),FVector2D(450.f,-2350.f))<1050.f)continue;
   const float Scale=bNorth?RegionRNG.FRandRange(.9f,1.5f):RegionRNG.FRandRange(.45f,.85f);
   Trunks->AddInstance(FTransform(FRotator::ZeroRotator,P+FVector(0,0,120.f*Scale),FVector(.18f*Scale,.18f*Scale,2.4f*Scale)));
   Canopies->AddInstance(FTransform(FRotator::ZeroRotator,P+FVector(0,0,250.f*Scale),FVector(1.1f*Scale,1.1f*Scale,1.8f*Scale)));
  }
 }
 // Location marker; gameplay actors are the only replicated interactive objects.
 AStaticMeshActor* Beacon=W->SpawnActor<AStaticMeshActor>(FVector(0,0,210),FRotator::ZeroRotator);
 if(Beacon){Beacon->SetReplicates(false);auto* M=Beacon->GetStaticMeshComponent();M->SetMobility(EComponentMobility::Movable);M->SetStaticMesh(Cylinder);Beacon->SetActorScale3D(FVector(1.3f,1.3f,4.2f));}
 UE_LOG(LogTemp,Display,TEXT("[NYVERRA Alpha 0.6] instanced forest generated locally"));
}
void ANyWorldState::CreateAtmosphere(){
 UWorld* W=GetWorld();
 if(!W)return;
 // Respect authored lighting in Basic/TestWorld. Spawning a second directional
 // light caused duplicate-sun warnings and inconsistent day/night rendering.
 for(TActorIterator<ADirectionalLight> It(W);It;++It){
  if(IsValid(*It)){Sun=*It;break;}
 }
 for(TActorIterator<AExponentialHeightFog> It(W);It;++It){
  if(IsValid(*It)){Fog=*It;break;}
 }
 if(!Sun){
  Sun=W->SpawnActor<ADirectionalLight>(FVector(0,0,1000),FRotator(-38,-32,0));
  if(Sun)Sun->SetReplicates(false);
 }
 if(!Fog){
  Fog=W->SpawnActor<AExponentialHeightFog>(FVector(0,0,0),FRotator::ZeroRotator);
  if(Fog)Fog->SetReplicates(false);
 }
 // Time of day updates transform and intensity, which require a movable sun.
 if(Sun){
  if(UDirectionalLightComponent* Light=Sun->GetComponent()){
   Light->SetMobility(EComponentMobility::Movable);
  }
 }
 UpdateAtmosphere();
}
void ANyWorldState::UpdateAtmosphere(){
 bLastEcho=bEchoActive;
 if(Sun){if(UDirectionalLightComponent* L=Sun->GetComponent()){
   const float Solar=FMath::Max(0.02f,FMath::Sin((TimeOfDayHours-6.f)*PI/12.f));
   L->SetWorldRotation(FRotator(90.f-180.f*(TimeOfDayHours/24.f),-32.f,0.f));
   L->SetIntensity((0.1f+6.f*Solar)*(bEchoActive?0.32f:1.f)*(bRainActive?0.65f:1.f));
   L->SetLightColor(bEchoActive?FLinearColor(.27f,.65f,.85f):FLinearColor(1.f,.94f,.8f));
 }}
 if(Fog){if(UExponentialHeightFogComponent* F=Fog->GetComponent()){
   F->SetFogDensity(bEchoActive?.065f:(bRainActive?.045f:.018f));
   F->SetFogInscatteringColor(bEchoActive?FLinearColor(.02f,.38f,.48f):(bRainActive?FLinearColor(.2f,.3f,.35f):FLinearColor(.40f,.55f,.64f)));
 }}
}
void ANyWorldState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyWorldState,bEchoActive);
 DOREPLIFETIME(ANyWorldState,EchoSeconds);
 DOREPLIFETIME(ANyWorldState,TimeOfDayHours);
 DOREPLIFETIME(ANyWorldState,bRainActive);
 DOREPLIFETIME(ANyWorldState,WeatherSeconds);
}
