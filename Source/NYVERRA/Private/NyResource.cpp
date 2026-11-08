#include "NyResource.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Net/UnrealNetwork.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/UObjectGlobals.h"
#include "TimerManager.h"
ANyResource::ANyResource() {
 bReplicates = true;
 SetReplicateMovement(false);
 Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ResourceMesh"));
 RootComponent=Mesh;
 Mesh->SetCollisionProfileName(TEXT("BlockAll"));
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
 if(Sphere.Succeeded()) Mesh->SetStaticMesh(Sphere.Object);
}
void ANyResource::Setup(ENyResourceKind NewKind,int32 Amount) {
 if(!HasAuthority()) return;
 Kind=NewKind;InitialRemaining=FMath::Max(1,Amount);Remaining=InitialRemaining;
 UpdateLook();UpdateAvailability();ForceNetUpdate();
}
void ANyResource::UpdateLook() {
 if(Kind==ENyResourceKind::Wood) SetActorScale3D(FVector(0.5f,0.5f,1.6f));
 else if(Kind==ENyResourceKind::Stone) SetActorScale3D(FVector(1.0f,0.85f,0.55f));
 else if(Kind==ENyResourceKind::Berries) SetActorScale3D(FVector(0.32f));
 else SetActorScale3D(FVector(0.45f));
 // Optional high-detail materials are loaded only after artists import
 // the VisualPolish assets. BasicShapes materials stay a safe fallback.
 if(Kind==ENyResourceKind::Stone || Kind==ENyResourceKind::Wood){
  const TCHAR* Path=Kind==ENyResourceKind::Stone?
   TEXT("/Game/NYVERRA/VisualPolish/Materials/M_NyRock_PBR056.M_NyRock_PBR056"):
   TEXT("/Game/NYVERRA/VisualPolish/Materials/M_NySoil_PBR056.M_NySoil_PBR056");
  if(UMaterialInterface* Surface=LoadObject<UMaterialInterface>(nullptr,Path)){
   Mesh->SetMaterial(0,Surface);
   return;
  }
 }
 if(UMaterialInstanceDynamic* Material=Mesh->CreateAndSetMaterialInstanceDynamic(0)) {
  const FLinearColor Color=Kind==ENyResourceKind::Wood?FLinearColor(0.20f,0.34f,0.13f):Kind==ENyResourceKind::Stone?FLinearColor(0.22f,0.29f,0.31f):Kind==ENyResourceKind::Berries?FLinearColor(0.7f,0.04f,0.12f):FLinearColor(0.0f,0.75f,0.9f);
  Material->SetVectorParameterValue(TEXT("Color"),Color);
 }
}
// Empty resource nodes are hidden and non-blocking on BOTH server and clients.
void ANyResource::UpdateAvailability(){
 if(!Mesh)return;
 const bool bAvailable=Remaining>0;
 Mesh->SetVisibility(bAvailable,true);
 Mesh->SetCollisionEnabled(bAvailable?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
}
void ANyResource::OnRep_Remaining(){UpdateAvailability();}
void ANyResource::OnRep_Kind(){UpdateLook();UpdateAvailability();}
bool ANyResource::Harvest(int32& Award,int32 Requested){
 Award=0;
 if(!HasAuthority()||Remaining<=0||Requested<1||Remaining<Requested)return false;
 Award=Requested;
 Remaining-=Requested;
 UpdateAvailability();
 if(Remaining==0){
  GetWorldTimerManager().SetTimer(RespawnTimer,this,&ANyResource::RespawnResource,RespawnSeconds,false);
 }
 ForceNetUpdate();
 return true;
}
void ANyResource::RespawnResource(){
 if(!HasAuthority())return;
 Remaining=FMath::Max(1,InitialRemaining);
 UpdateAvailability();
 ForceNetUpdate();
}
void ANyResource::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyResource,Remaining);DOREPLIFETIME(ANyResource,Kind);
}
