#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "NyCharacter.generated.h"
class UCameraComponent;
class UNyPlayerSaveGame;
UENUM(BlueprintType)
// Append new item IDs only: numeric IDs 0-6 are already stored in SaveGame v1.
enum class ENyItemId : uint8 { Wood, Stone, EchoShard, Berries, Axe, Pickaxe, Water, Bandage };
USTRUCT(BlueprintType)
struct FNyItemStack {
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadOnly) ENyItemId Item = ENyItemId::Wood;
 UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 Quantity = 0;
};
UCLASS()
class NYVERRA_API ANyCharacter : public ACharacter {
 GENERATED_BODY()
public:
 ANyCharacter();
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
 virtual void BeginPlay() override;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) UCameraComponent* Camera;
 UPROPERTY(Replicated,BlueprintReadOnly) int32 Wood=0;
 UPROPERTY(Replicated,BlueprintReadOnly) int32 Stone=0;
 UPROPERTY(Replicated,BlueprintReadOnly) int32 Echo=0;
 UPROPERTY(Replicated,BlueprintReadOnly) int32 Berries=0;
 UPROPERTY(Replicated,BlueprintReadOnly) float Thirst=100.f;
 UPROPERTY(Replicated,BlueprintReadOnly) float Stamina=100.f;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Inventory") TArray<FNyItemStack> Inventory;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Inventory") int32 MaxSlots = 16;
 UFUNCTION(Server,Reliable) void ServerCraft(uint8 RecipeId);
 UFUNCTION(Server,Reliable) void ServerEatBerries();
 UFUNCTION(Server,Reliable) void ServerDrinkWater();
 UFUNCTION(Server,Reliable) void ServerCraftBandage();
 UFUNCTION(Server,Reliable) void ServerUseBandage();
 int32 CountItem(ENyItemId Item) const;
 // Server-only loot insertion with full inventory capacity validation.
 bool GiveLoot(ENyItemId Item,int32 Quantity);
 // Only authoritative GameMode may capture/apply persistent character state.
 bool CapturePersistentState(UNyPlayerSaveGame* Save) const;
 bool ApplyPersistentState(const UNyPlayerSaveGame* Save);
 UFUNCTION(Server,Reliable) void ServerInteract();
 UFUNCTION(Server,Reliable) void ServerPlacePiece(uint8 Type);
 UFUNCTION(Server,Reliable) void ServerRepairPiece();
 UPROPERTY(Replicated,BlueprintReadOnly) float Health=100.f;
 UPROPERTY(Replicated,BlueprintReadOnly) float Hunger=100.f;
 virtual void Tick(float DeltaSeconds) override;
 // Alpha 0.11 server-authoritative melee combat, death and respawn.
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Combat") bool bIsDead=false;
 UPROPERTY(Replicated, BlueprintReadOnly, Category="Combat") int32 DeathCount=0;
 UFUNCTION(Server, Reliable) void ServerMeleeAttack();
 void ReceiveCombatDamage(float Amount, ANyCharacter* Attacker);
 UFUNCTION(Server,Reliable) void ServerSetSprint(bool bSprinting);
 virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
private:
 void Forward(float Value);
 void Right(float Value);
 void TryJump();
 void StopJumpIfAlive();
 void StartSprint();
 void StopSprint();
 void Interact();
 void PlaceFoundation();
 void PlaceWall();
 void PlaceDoor();
 void RepairPiece();
 void EatBerries();
 void DrinkWater();
 void CraftBandage();
 void UseBandage();
 void CraftAxe();
 void CraftPickaxe();
 void MeleeAttack();
 void RespawnAfterDeath();
 float LastAttackTime=-100.f;
 FTimerHandle RespawnTimer;
 bool AddItem(ENyItemId Item, int32 Quantity);
 bool SpendItems(ENyItemId A, int32 ACount, ENyItemId B, int32 BCount);
 void RefreshLegacyCounters();
 UPROPERTY(ReplicatedUsing=OnRep_Sprint) bool bWantsSprint=false;
 UFUNCTION() void OnRep_Sprint();
 float SurvivalAccumulator=0.f;
 float LastInteractionTime=-100.f;
 float LastDrinkTime=-100.f;
 float LastCraftTime=-100.f;
 float LastBandageTime=-100.f;
 float LastBuildTime=-100.f;
 float LastRepairTime=-100.f;
 void ToggleMouse();
 void ToggleInventory();
 bool bMouseFree=false;
public:
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inventory") bool bInventoryOpen=false;
 static FString GetItemName(ENyItemId Item);
};
