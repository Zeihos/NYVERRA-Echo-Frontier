#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NyCharacter.h"
#include "NyLootCrate.generated.h"
class UStaticMeshComponent;
UCLASS()
class NYVERRA_API ANyLootCrate : public AActor {
 GENERATED_BODY()
public:
 ANyLootCrate();
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) UStaticMeshComponent* Mesh;
 UPROPERTY(ReplicatedUsing=OnRep_LootState, BlueprintReadOnly) bool bAvailable=true;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) ENyItemId RewardItem=ENyItemId::Stone;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 RewardCount=4;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) float RespawnSeconds=180.f;
 void Configure(ENyItemId Item, int32 Count, float Seconds);
 bool TryLoot(class ANyCharacter* Player);
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out)const override;
protected:
 UFUNCTION() void OnRep_LootState();
private:
 FTimerHandle RespawnTimer;
 void RespawnLoot();
 void ApplyAppearance();
};
