#include "NyBuildPiece.h"
#include "NyCharacter.h"
#include "NyGameMode.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/OnlineReplStructs.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
#include "TimerManager.h"
#include "Engine/EngineTypes.h"

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
 if(!HasAuthority()||NewType>2||!IsValid(InBuilder))return;
 PieceType=NewType;
 PersistentId=FGuid::NewGuid();
 BuilderNetworkId=OnlineOwnerKey(InBuilder);
 MaxDurability=NewType==0?600.f:NewType==1?360.f:280.f;
 Durability=MaxDurability;
 BuilderPlayerState=InBuilder;
 LastDamageTime=-1000.f;
 bDoorOpen=false;
 OnRep_Type();
 OnRep_DoorOpen();
 ForceNetUpdate();
 if(ANyGameMode* GM=GetWorld()->GetAuthGameMode<ANyGameMode>()) GM->RequestBaseSave();
}

FString ANyBuildPiece::OnlineOwnerKey(const APlayerState* Player){
 if(!IsValid(Player))return FString();
 const FUniqueNetIdRepl& NetId=Player->GetUniqueId();
 // Display names and client-provided values are never owner credentials.
 return NetId.IsValid()?NetId.ToString():FString();
}

bool ANyBuildPiece::IsBuildOwner(const APlayerState* Player) const{
 if(!HasAuthority()||!IsValid(Player))return false;
 if(BuilderPlayerState==Player)return true;
 if(BuilderNetworkId.IsEmpty())return false;
 const FString Key=OnlineOwnerKey(Player);
 return !Key.IsEmpty() && Key==BuilderNetworkId;
}

void ANyBuildPiece::BindReturningOwner(APlayerState* Player){
 if(!HasAuthority()||!IsValid(Player)||BuilderNetworkId.IsEmpty())return;
 const FString Key=OnlineOwnerKey(Player);
 if(!Key.IsEmpty() && Key==BuilderNetworkId && BuilderPlayerState!=Player){
  BuilderPlayerState=Player;
  ForceNetUpdate();
 }
}

void ANyBuildPiece::UnbindDepartingOwner(const APlayerState* Player){
 if(!HasAuthority()||!IsValid(Player)||BuilderPlayerState!=Player)return;
 BuilderPlayerState=nullptr;
 ForceNetUpdate();
}

void ANyBuildPiece::RestoreFromSave(uint8 NewType, const FGuid& SavedId,
                                   float SavedDurability, const FString& SavedOwnerKey){
 if(!HasAuthority()||NewType>2||!SavedId.IsValid())return;
 PieceType=NewType;
 PersistentId=SavedId;
 MaxDurability=NewType==0?600.f:NewType==1?360.f:280.f;
 Durability=FMath::Clamp(SavedDurability,1.f,MaxDurability);
 BuilderNetworkId=SavedOwnerKey;
 BuilderPlayerState=nullptr; // Rebound in GameMode::PostLogin by online ID.
 bDoorOpen=false;             // Doors restart closed, never blocking in an open state.
 LastDamageTime=-1000.f;
 OnRep_Type();
 OnRep_DoorOpen();
 ForceNetUpdate();
}

void ANyBuildPiece::OnRep_Type(){
 // Initial scale must match authoritative overlap bounds on the server:
 // foundation 300x300x30; wall 240x30x250; door 180x25x240 cm.
 SetActorScale3D(PieceType==0?FVector(3.f,3.f,.3f):
   PieceType==1?FVector(2.4f,.3f,2.5f):FVector(1.8f,.25f,2.4f));
 OnRep_DoorOpen();
}

void ANyBuildPiece::OnRep_DoorOpen(){
 if(!Mesh)return;
 const bool bOpened=PieceType==2&&bDoorOpen;
 // Early prototype: while open the slab retracts completely. Unlike a
 // hidden collider it cannot trap a player walking through the doorway.
 Mesh->SetVisibility(!bOpened,true);
 Mesh->SetCollisionEnabled(bOpened?ECollisionEnabled::NoCollision:
   ECollisionEnabled::QueryAndPhysics);
}

bool ANyBuildPiece::TryOpenDoor(const APlayerState* Requester){
 if(!HasAuthority()||PieceType!=2||bDoorOpen||Durability<=0.f||
    !IsBuildOwner(Requester)||!GetWorld())return false;
 bDoorOpen=true;
 OnRep_DoorOpen();
 ForceNetUpdate();
 GetWorldTimerManager().SetTimer(DoorCloseTimer,this,
   &ANyBuildPiece::TryCloseDoor,8.f,false);
 return true;
}

void ANyBuildPiece::TryCloseDoor(){
 if(!HasAuthority()||PieceType!=2||!bDoorOpen||!GetWorld())return;
 // Don't trap a player inside the reappearing closed doorway.
 // Vertical safety volume deliberately stops above its supporting foundation.
 FCollisionObjectQueryParams Objects;
 Objects.AddObjectTypesToQuery(ECC_Pawn);
 Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
 FCollisionQueryParams Query(SCENE_QUERY_STAT(NyDoorSafety),false,this);
 const bool bOccupied=GetWorld()->OverlapAnyTestByObjectType(
   GetActorLocation(),GetActorQuat(),Objects,
   FCollisionShape::MakeBox(FVector(95.f,70.f,105.f)),Query);
 if(bOccupied){
  GetWorldTimerManager().SetTimer(DoorCloseTimer,this,
    &ANyBuildPiece::TryCloseDoor,1.f,false);
  return;
 }
 bDoorOpen=false;
 OnRep_DoorOpen();
 ForceNetUpdate();
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
 if(ANyGameMode* GM=GetWorld()->GetAuthGameMode<ANyGameMode>()) GM->RequestBaseSave();
 if(Durability<=0.f){
  // A destroyed base piece cannot be looted repeatedly or used for physics.
  // Replicated Actor destruction removes it from every connected client.
  Destroy();
 }
 return Applied;
}

bool ANyBuildPiece::CanRepair(const APlayerState* Requester) const{
 if(!HasAuthority()||!IsBuildOwner(Requester)||
    Durability<=0.f||Durability>=MaxDurability||!GetWorld())return false;
 return GetWorld()->GetTimeSeconds()-LastDamageTime>=12.f;
}

bool ANyBuildPiece::Repair(const APlayerState* Requester,float Amount){
 if(!CanRepair(Requester)||!FMath::IsFinite(Amount)||Amount<=0.f)return false;
 Durability=FMath::Min(MaxDurability,Durability+FMath::Min(Amount,75.f));
 ForceNetUpdate();
 if(ANyGameMode* GM=GetWorld()->GetAuthGameMode<ANyGameMode>()) GM->RequestBaseSave();
 return true;
}

void ANyBuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyBuildPiece,PieceType);
 DOREPLIFETIME(ANyBuildPiece,Durability);
 DOREPLIFETIME(ANyBuildPiece,MaxDurability);
 DOREPLIFETIME(ANyBuildPiece,BuilderPlayerState);
 DOREPLIFETIME(ANyBuildPiece,PersistentId);
 DOREPLIFETIME(ANyBuildPiece,bDoorOpen);
}
