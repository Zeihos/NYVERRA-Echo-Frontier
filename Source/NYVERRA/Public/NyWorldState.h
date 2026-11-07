#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "NyWorldState.generated.h"

UCLASS()
class NYVERRA_API ANyWorldState : public AGameStateBase {
 GENERATED_BODY()
public:
 ANyWorldState();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
 UPROPERTY(Replicated,BlueprintReadOnly,Category="Echo") bool bEchoActive=false;
 UPROPERTY(Replicated,BlueprintReadOnly,Category="Echo") int32 EchoSeconds=90;
 // Server-driven world clock, 0..24 hours. Clients never mutate these values.
 UPROPERTY(Replicated,BlueprintReadOnly,Category="Environment") float TimeOfDayHours=10.f;
 UPROPERTY(Replicated,BlueprintReadOnly,Category="Environment") bool bRainActive=false;
 UPROPERTY(Replicated,BlueprintReadOnly,Category="Environment") int32 WeatherSeconds=160;
private:
 float Accumulator=0.f;
 void GenerateLocalTerrain();
 void CreateCollisionGround();
 void CreateExplorationSites();
 void CreateAtmosphere();
 void UpdateAtmosphere();
 UPROPERTY(Transient) class UHierarchicalInstancedStaticMeshComponent* Trunks=nullptr;
 UPROPERTY(Transient) class UHierarchicalInstancedStaticMeshComponent* Canopies=nullptr;
 UPROPERTY(Transient) class UHierarchicalInstancedStaticMeshComponent* Rocks=nullptr;
 UPROPERTY(Transient) class ADirectionalLight* Sun=nullptr;
 UPROPERTY(Transient) class AExponentialHeightFog* Fog=nullptr;
 bool bLastEcho=false;
 float VisualUpdateAccumulator=0.f;
};
