#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NyResource.generated.h"
class UStaticMeshComponent;
UENUM(BlueprintType)
enum class ENyResourceKind : uint8 { Wood, Stone, EchoShard, Berries, Water };
UCLASS()
class NYVERRA_API ANyResource : public AActor {
 GENERATED_BODY()
public:
 ANyResource();
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) UStaticMeshComponent* Mesh;
 UPROPERTY(ReplicatedUsing=OnRep_Remaining, BlueprintReadOnly) int32 Remaining = 5;
 UPROPERTY(ReplicatedUsing=OnRep_Kind, BlueprintReadOnly) ENyResourceKind Kind = ENyResourceKind::Wood;
 UFUNCTION() void OnRep_Remaining();
 UFUNCTION() void OnRep_Kind();
 void Setup(ENyResourceKind NewKind, int32 Amount);
 bool Harvest(int32& Award, int32 Requested=1);
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
private:
 // InitialRemaining is authoritative server state; no client-side timers.
 int32 InitialRemaining = 5;
 FTimerHandle RespawnTimer;
 UPROPERTY(EditDefaultsOnly, Category="Resource") float RespawnSeconds = 120.f;
 void RespawnResource();
 void UpdateLook();
 void UpdateAvailability();
};
