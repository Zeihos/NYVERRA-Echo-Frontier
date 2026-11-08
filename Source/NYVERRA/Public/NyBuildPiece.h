#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NyBuildPiece.generated.h"

class UStaticMeshComponent;
class APlayerState;

UCLASS()
class NYVERRA_API ANyBuildPiece : public AActor {
 GENERATED_BODY()
public:
 ANyBuildPiece();

 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Building")
 UStaticMeshComponent* Mesh;

 // 0 = foundation, 1 = wall, 2 = locked door (all dimensions in cm).
 UPROPERTY(ReplicatedUsing=OnRep_Type, BlueprintReadOnly, Category="Building")
 uint8 PieceType=0;

 // All durability and ownership changes are made exclusively on the server.
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Building")
 float Durability=600.f;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Building")
 float MaxDurability=600.f;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Building")
 APlayerState* BuilderPlayerState=nullptr;

 // Type 2 only. An open door is temporarily non-blocking and closes on a
 // server timer once the doorway is clear of characters.
 UPROPERTY(ReplicatedUsing=OnRep_DoorOpen, BlueprintReadOnly, Category="Building")
 bool bDoorOpen=false;
 UFUNCTION() void OnRep_DoorOpen();
 bool TryOpenDoor(const APlayerState* Requester);

 void Initialize(uint8 NewType, APlayerState* InBuilder);
 UFUNCTION() void OnRep_Type();

 // Repairs are limited to the builder's active PlayerState in this prototype.
 // Combat repairs are locked for 12 seconds after the last hit.
 bool CanRepair(const APlayerState* Requester) const;
 bool Repair(const APlayerState* Requester, float Amount);

 virtual float TakeDamage(float DamageAmount, const struct FDamageEvent& DamageEvent,
                          class AController* EventInstigator, AActor* DamageCauser) override;
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out)const override;

private:
 float LastDamageTime=-1000.f;
 FTimerHandle DoorCloseTimer;
 void TryCloseDoor();
};
