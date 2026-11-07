#include "NyBuildPiece.h"
#include "Components/StaticMeshComponent.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
ANyBuildPiece::ANyBuildPiece(){
 bReplicates=true;SetReplicateMovement(true);
 Mesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BuildMesh"));RootComponent=Mesh;
 Mesh->SetCollisionProfileName(TEXT("BlockAll"));
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
 if(Cube.Succeeded())Mesh->SetStaticMesh(Cube.Object);
 // The initial replicated PieceType is 0 (foundation). OnRep_Type will not fire
 // on a newly connected client when that property equals its default value.
 // Initialize the correct 300x300x30 cm foundation size on both server and clients.
 SetActorScale3D(FVector(3.f,3.f,.3f));
}
void ANyBuildPiece::Initialize(uint8 NewType){if(!HasAuthority())return;PieceType=NewType;OnRep_Type();ForceNetUpdate();}
void ANyBuildPiece::OnRep_Type(){
 // 0: foundation 300x300x30; 1: wall 300x30x250
 SetActorScale3D(PieceType==0?FVector(3.f,3.f,.3f):FVector(3.f,.3f,2.5f));
}
void ANyBuildPiece::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out)const{
 Super::GetLifetimeReplicatedProps(Out);DOREPLIFETIME(ANyBuildPiece,PieceType);
}
