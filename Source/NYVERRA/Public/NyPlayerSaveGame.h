#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "NyPlayerSaveGame.generated.h"

// Keep the persistent schema independent of runtime replicated USTRUCTs.
USTRUCT()
struct FNySavedPlayerStack
{
 GENERATED_BODY()
 UPROPERTY(SaveGame) uint8 ItemId=0;
 UPROPERTY(SaveGame) int32 Quantity=0;
};

UCLASS()
class NYVERRA_API UNyPlayerSaveGame : public USaveGame
{
 GENERATED_BODY()
public:
 UPROPERTY(SaveGame) int32 FormatVersion=1;
 UPROPERTY(SaveGame) int64 SaveRevision=0;
 UPROPERTY(SaveGame) FString MapName;
 // A digest is only a filename/record key, NOT an authentication method.
 UPROPERTY(SaveGame) FString OwnerDigest;
 UPROPERTY(SaveGame) float Health=100.f;
 UPROPERTY(SaveGame) float Hunger=100.f;
 UPROPERTY(SaveGame) float Thirst=100.f;
 UPROPERTY(SaveGame) float Stamina=100.f;
 UPROPERTY(SaveGame) int32 DeathCount=0;
 UPROPERTY(SaveGame) bool bWasDead=false;
 UPROPERTY(SaveGame) TArray<FNySavedPlayerStack> Inventory;
};
