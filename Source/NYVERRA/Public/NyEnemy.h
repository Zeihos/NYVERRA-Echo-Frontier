#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "NyEnemy.generated.h"

// Prototype PvE creature. The server owns AI, health and attacks.
UCLASS()
class NYVERRA_API ANyEnemy : public ACharacter {
 GENERATED_BODY()
public:
 ANyEnemy();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent, class AController* EventInstigator, AActor* DamageCauser) override;
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Enemy") float Health = 60.f;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Enemy") bool bDead = false;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") float AggroRadius = 1100.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") float AttackRadius = 145.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") float PatrolRadius = 550.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") float LeashRadius = 1750.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Enemy") float LootDropChance = 1.f;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Enemy") bool bAlerted = false;
private:
 UPROPERTY(VisibleAnywhere, Category="Enemy|Visual") TObjectPtr<class UStaticMeshComponent> DebugBody;
 void Think();
 TWeakObjectPtr<class ANyCharacter> Target;
 float LastAttackTime = -100.f;
 float NextSearchTime = 0.f;
 FVector HomeLocation = FVector::ZeroVector;
 FVector PatrolPoint = FVector::ZeroVector;
 float NextPatrolChoice = 0.f;
 void MoveToward(const FVector& Destination);
 float NextPathRequestTime = 0.f;
 FVector LastPathDestination = FVector(1000000.f,1000000.f,1000000.f);
 FTimerHandle DespawnTimer;
};
