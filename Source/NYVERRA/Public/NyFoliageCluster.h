#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NyFoliageCluster.generated.h"

class UHierarchicalInstancedStaticMeshComponent;

/** Decorative, non-interactive foliage. Harvestable trees must remain separate replicated actors. */
UCLASS(BlueprintType)
class NYVERRA_API ANyFoliageCluster : public AActor
{
    GENERATED_BODY()
public:
    ANyFoliageCluster();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="NYVERRA|Foliage")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Trees;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="NYVERRA|Foliage")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Rocks;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="NYVERRA|Foliage")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Shrubs;

    /** Kind is Tree, Rock or Shrub. Transform is in world space. Returns false for unknown kinds. */
    UFUNCTION(BlueprintCallable, CallInEditor, Category="NYVERRA|Foliage")
    bool AddFoliageInstance(FName Kind, FTransform WorldTransform);

    UFUNCTION(BlueprintCallable, CallInEditor, Category="NYVERRA|Foliage")
    void ClearFoliage();
};
