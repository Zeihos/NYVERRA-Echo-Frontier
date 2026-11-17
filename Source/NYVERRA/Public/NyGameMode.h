#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NyGameMode.generated.h"

class APlayerState;
class APlayerController;

UCLASS()
class NYVERRA_API ANyGameMode : public AGameModeBase {
 GENERATED_BODY()
public:
 ANyGameMode();
 virtual void BeginPlay() override;
 virtual void PostLogin(APlayerController* NewPlayer) override;
 virtual void Logout(AController* Exiting) override;
 // Called exclusively by server-side build/damage/repair mutations.
 void RequestBaseSave();

private:
 void SpawnServerResources();
 void SpawnSiteResources();
 void SpawnSiteLoot();
 void SpawnEnemies();

 bool ShouldPersistBases() const;
 FString BaseSlotName() const;
 void LoadBases();
 void SaveBases();
 void BindPlayerToSavedBases(APlayerState* Player);

 FTimerHandle BaseAutosaveTimer;
 FTimerHandle BaseDirtySaveTimer;
 bool bLoadingBases=false;
 // Unknown/incompatible/corrupt save files are never overwritten.
 bool bBaseSaveReadOnly=false;
};
