#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "NyBaseSaveGame.generated.h"

// Schema v1: never store runtime actor pointers in long-lived saves.
USTRUCT(BlueprintType)
struct FNySavedBuildPiece
{
 GENERATED_BODY()

 UPROPERTY(SaveGame) FGuid PersistentId;
 UPROPERTY(SaveGame) uint8 PieceType=0;
 UPROPERTY(SaveGame) FVector Location=FVector::ZeroVector;
 UPROPERTY(SaveGame) FRotator Rotation=FRotator::ZeroRotator;
 UPROPERTY(SaveGame) float Durability=0.f;

 // Server-only online identity from the configured OnlineSubsystem, NOT
 // a display name, client-supplied field or replicated property.
 UPROPERTY(SaveGame) FString OwnerNetworkId;
};

UCLASS()
class NYVERRA_API UNyBaseSaveGame : public USaveGame
{
 GENERATED_BODY()
public:
 UPROPERTY(SaveGame) int32 FormatVersion=1;
 UPROPERTY(SaveGame) FString MapName;
 UPROPERTY(SaveGame) TArray<FNySavedBuildPiece> Pieces;
};
