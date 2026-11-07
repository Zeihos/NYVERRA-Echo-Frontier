#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NyGameMode.generated.h"
UCLASS()
class NYVERRA_API ANyGameMode : public AGameModeBase {
 GENERATED_BODY()
public:
 ANyGameMode();
 virtual void InitGame(const FString& MapName,const FString& Options,FString& ErrorMessage) override;
 virtual void BeginPlay() override;
private:
 void SpawnServerResources();
 void SpawnSiteResources();
 void SpawnSiteLoot();
 void SpawnEnemies();
};
