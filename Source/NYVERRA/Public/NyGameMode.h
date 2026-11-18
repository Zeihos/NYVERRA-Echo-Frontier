#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NyGameMode.generated.h"

class APlayerState;
class APlayerController;
class ANyCharacter;

UCLASS()
class NYVERRA_API ANyGameMode : public AGameModeBase {
 GENERATED_BODY()
public:
 ANyGameMode();
 virtual void BeginPlay() override;
 virtual void PostLogin(APlayerController* NewPlayer) override;
 virtual void RestartPlayer(AController* NewPlayer) override;
 virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
 virtual void Logout(AController* Exiting) override;
 // Called exclusively by server-side build/damage/repair mutations.
 void RequestBaseSave();
 // Debounced server-only player inventory/survival save.
 void RequestPlayerSave();
 // Write a death-state checkpoint synchronously before the respawn timer.
 void CheckpointPlayerDeath(ANyCharacter* Player);
 // Fail closed if an incompatible save was detected: do not charge players
 // for structures that cannot be written back to the same save slot.
 bool CanPlaceBasePieces() const { return CanMutateBaseWorld(); }
 bool CanMutateBaseWorld() const { return !bBaseSaveReadOnly; }

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
 bool ShouldPersistPlayers() const;
 FString PlayerPersistenceKey(const APlayerState* Player) const;
 FString PlayerSaveSlot(const FString& Key) const;
 bool HasDuplicatePlayerIdentity(const ANyCharacter* Pawn,const FString& Key) const;
 void LoadPlayerState(ANyCharacter* Player);
 void SavePlayerState(ANyCharacter* Player);
 void SaveActivePlayers();

 FTimerHandle PlayerAutosaveTimer;
 FTimerHandle PlayerDirtySaveTimer;
 TMap<FString,int64> PlayerSaveRevisions;
 TMap<FString,bool> PlayerNextBackup;
 TSet<FString> ProtectedPlayerSlots;
 TSet<AController*> PlayerLoadAttemptedControllers;
 bool bLoadingPlayerState=false;
 FTimerHandle BaseAutosaveTimer;
 FTimerHandle BaseDirtySaveTimer;
 bool bLoadingBases=false;
 // Alternate A/B slots. The v1 A slot remains readable without migration.
 int64 BaseSaveRevision=0;
 bool bNextSaveToBackup=false;
 // Unknown/incompatible/corrupt save files are never overwritten.
 bool bBaseSaveReadOnly=false;
};
