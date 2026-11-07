#include "NyFoliageCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "UObject/ConstructorHelpers.h"

ANyFoliageCluster::ANyFoliageCluster()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false; // Only fixed decorative instances; no gameplay state or interaction.
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);

    Trees = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Trees"));
    Rocks = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Rocks"));
    Shrubs = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Shrubs"));

    for (UHierarchicalInstancedStaticMeshComponent* Component : {Trees.Get(), Rocks.Get(), Shrubs.Get()})
    {
        Component->SetupAttachment(Root);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetMobility(EComponentMobility::Static);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (Cone.Succeeded()) Trees->SetStaticMesh(Cone.Object);
    if (Sphere.Succeeded())
    {
        Rocks->SetStaticMesh(Sphere.Object);
        Shrubs->SetStaticMesh(Sphere.Object);
    }
}

bool ANyFoliageCluster::AddFoliageInstance(FName Kind, FTransform WorldTransform)
{
    UHierarchicalInstancedStaticMeshComponent* Target = nullptr;
    if (Kind == TEXT("Tree")) Target = Trees;
    else if (Kind == TEXT("Rock")) Target = Rocks;
    else if (Kind == TEXT("Shrub")) Target = Shrubs;
    if (!Target || !WorldTransform.IsValid()) return false;
    Target->AddInstance(WorldTransform, true);
    return true;
}

void ANyFoliageCluster::ClearFoliage()
{
    Trees->ClearInstances();
    Rocks->ClearInstances();
    Shrubs->ClearInstances();
}
