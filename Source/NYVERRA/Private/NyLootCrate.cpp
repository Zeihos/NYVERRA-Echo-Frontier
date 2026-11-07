#include "NyLootCrate.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include "Engine/World.h"
ANyLootCrate::ANyLootCrate(){
 bReplicates=true; SetReplicateMovement(false);
 Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LootCrateMesh"));RootComponent=Mesh;
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
 if(Cube.Succeeded())Mesh->SetStaticMesh(Cube.Object);
 Mesh->SetRelativeScale3D(FVector(0.95f,0.7f,0.65f));
 Mesh->SetCollisionProfileName(TEXT("BlockAll"));
}
void ANyLootCrate::Configure(ENyItemId Item,int32 Count,float Seconds){
 if(!HasAuthority())return;
 RewardItem=Item;RewardCount=FMath::Clamp(Count,1,100);RespawnSeconds=FMath::Max(10.f,Seconds);
}
bool ANyLootCrate::TryLoot(ANyCharacter* Player){
 if(!HasAuthority()||!bAvailable||!IsValid(Player)||Player->Health<=0.f)return false;
 if(FVector::DistSquared(Player->GetActorLocation(),GetActorLocation())>FMath::Square(350.f))return false;
 if(!Player->GiveLoot(RewardItem,RewardCount))return false;
 bAvailable=false;ApplyAppearance();ForceNetUpdate();
 GetWorldTimerManager().SetTimer(RespawnTimer,this,&ANyLootCrate::RespawnLoot,RespawnSeconds,false);
 return true;
}
void ANyLootCrate::RespawnLoot(){if(!HasAuthority())return;bAvailable=true;ApplyAppearance();ForceNetUpdate();}
void ANyLootCrate::OnRep_LootState(){ApplyAppearance();}
void ANyLootCrate::ApplyAppearance(){
 if(!Mesh)return;
 Mesh->SetVisibility(bAvailable,true);
 // A looted (invisible) crate must not block walking, melee traces or building.
 Mesh->SetCollisionEnabled(bAvailable?ECollisionEnabled::QueryAndPhysics:ECollisionEnabled::NoCollision);
}
void ANyLootCrate::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);DOREPLIFETIME(ANyLootCrate,bAvailable);
}
