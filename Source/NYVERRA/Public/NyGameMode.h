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
 // Fail closed if an incompatible save was detected: do not charge players
 // for structures that cannot be written back to the same save slot.
 bool CanPlaceBasePieces() const { return !bBaseSaveReadOnly; }

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
 // Alternate A/B slots. The v1 A slot remains readable without migration.
 int64 BaseSaveRevision=0;
 bool bNextSaveToBackup=false;
 // Unknown/incompatible/corrupt save files are never overwritten.
 bool bBaseSaveReadOnly=false;
};
