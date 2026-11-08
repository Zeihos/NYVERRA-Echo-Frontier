#include "NyBuildPiece.h"
#include "NyCharacter.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerState.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"

ANyBuildPiece::ANyBuildPiece(){
 bReplicates=true;
 SetReplicateMovement(true);
 Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BuildMesh"));
 RootComponent=Mesh;
 Mesh->SetCollisionProfileName(TEXT("BlockAll"));
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
 if(Cube.Succeeded())Mesh->SetStaticMesh(Cube.Object);
 // Type zero is the default: its OnRep may never fire on new clients.
 SetActorScale3D(FVector(3.f,3.f,.3f));
}

void ANyBuildPiece::Initialize(uint8 NewType,APlayerState* InBuilder){
 if(!HasAuthority()||NewType>1)return;
 PieceType=NewType;
 MaxDurability=NewType==0?600.f:360.f;
 Durability=MaxDurability;
 BuilderPlayerState=InBuilder;
 LastDamageTime=-1000.f;
 OnRep_Type();
 ForceNetUpdate();
}

void ANyBuildPiece::OnRep_Type(){
 // Keep collision dimensions matched to the authoritative placement checks:
 // foundation 300 x 300 x 30; wall 240 x 30 x 250 centimeters.
 SetActorScale3D(PieceType==0?FVector(3.f,3.f,.3f):FVector(2.4f,.3f,2.5f));
}

float ANyBuildPiece::TakeDamage(float DamageAmount,const FDamageEvent& DamageEvent,
                               AController* EventInstigator,AActor* DamageCauser){
 if(!HasAuthority()||Durability<=0.f||!FMath::IsFinite(DamageAmount)||DamageAmount<=0.f)
  return 0.f;
 // Only a living server-controlled player may damage structures in this
 // initial melee raid loop. Clients cannot set Durability or bypass cover.
 const ANyCharacter* Raider=Cast<ANyCharacter>(DamageCauser);
 if(!IsValid(Raider)||Raider->bIsDead||Raider->Health<=0.f||
    !EventInstigator||Raider->GetController()!=EventInstigator)
  return 0.f;
 const float Applied=FMath::Min(Durability,FMath::Min(DamageAmount,50.f));
 Durability=FMath::Max(0.f,Durability-Applied);
 LastDamageTime=GetWorld()->GetTimeSeconds();
 ForceNetUpdate();
 if(Durability<=0.f){
  // A destroyed base piece cannot be looted repeatedly or used for physics.
  // Replicated Actor destruction removes it from every connected client.
  Destroy();
 }
 return Applied;
}

bool ANyBuildPiece::CanRepair(const APlayerState* Requester) const{
 if(!HasAuthority()||!IsValid(Requester)||BuilderPlayerState!=Requester||
    Durability<=0.f||Durability>=MaxDurability||!GetWorld())return false;
 return GetWorld()->GetTimeSeconds()-LastDamageTime>=12.f;
}

bool ANyBuildPiece::Repair(const APlayerState* Requester,float Amount){
 if(!CanRepair(Requester)||!FMath::IsFinite(Amount)||Amount<=0.f)return false;
 Durability=FMath::Min(MaxDurability,Durability+FMath::Min(Amount,75.f));
 ForceNetUpdate();
 return true;
}

void ANyBuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyBuildPiece,PieceType);
 DOREPLIFETIME(ANyBuildPiece,Durability);
 DOREPLIFETIME(ANyBuildPiece,MaxDurability);
 DOREPLIFETIME(ANyBuildPiece,BuilderPlayerState);
}
