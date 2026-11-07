#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NyBuildPiece.generated.h"
class UStaticMeshComponent;
UCLASS()
class NYVERRA_API ANyBuildPiece : public AActor {
 GENERATED_BODY()
public:
 ANyBuildPiece();
 UPROPERTY(VisibleAnywhere) UStaticMeshComponent* Mesh;
 UPROPERTY(ReplicatedUsing=OnRep_Type,BlueprintReadOnly) uint8 PieceType=0;
 void Initialize(uint8 NewType);
 UFUNCTION() void OnRep_Type();
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out)const override;
};
