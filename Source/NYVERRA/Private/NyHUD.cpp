#include "NyHUD.h"
#include "NyCharacter.h"
#include "NyWorldState.h"
#include "Engine/World.h"
#include "Engine/Canvas.h"
#include "GameFramework/PlayerController.h"
void ANyHUD::DrawHUD(){
 Super::DrawHUD();
 if(!Canvas)return;
 const float X=Canvas->SizeX,Y=Canvas->SizeY;
 DrawText(TEXT("NYVERRA  /  ECHO FRONTIER   -   ALPHA 0.11"),FLinearColor(0.1f,0.9f,0.9f),28,28,nullptr,1.2f);
 DrawText(TEXT("WASD move  |  mouse look  |  Space jump  |  Shift sprint  |  LMB attack  |  E gather  |  1 foundation  |  2 wall  |  F eat berries  |  3 axe  |  4 pickaxe  |  I inventory  |  Tab cursor"),FLinearColor::White,28,63);
 if(const ANyCharacter* P=Cast<ANyCharacter>(GetOwningPawn())){
  const FString Info=FString::Printf(TEXT("WOOD  %d     STONE  %d     ECHO  %d     BERRIES  %d"),P->Wood,P->Stone,P->Echo,P->Berries);
  FString Slots=FString::Printf(TEXT("INVENTORY %d / %d  |  AXE %d  |  PICKAXE %d"),P->Inventory.Num(),P->MaxSlots,P->CountItem(ENyItemId::Axe),P->CountItem(ENyItemId::Pickaxe));
  DrawText(Slots,FLinearColor(.8f,.9f,1.f),28,Y-133);
  if(P->bInventoryOpen){
   const float Cell=70.f, Gap=7.f, GridW=4*Cell+3*Gap;
   const float Left=(X-GridW)*.5f, Top=(Y-4*Cell-3*Gap)*.5f;
   DrawRect(FLinearColor(.015f,.025f,.036f,.94f),Left-24,Top-90,GridW+48,4*Cell+3*Gap+185);
   DrawText(TEXT("INVENTORY  -  16 SLOTS"),FLinearColor(.38f,.95f,.88f),Left,Top-65,nullptr,1.2f);
   for(int32 Index=0;Index<P->MaxSlots;++Index){
    const float SX=Left+(Index%4)*(Cell+Gap),SY=Top+(Index/4)*(Cell+Gap);
    DrawRect(FLinearColor(.09f,.15f,.19f,.95f),SX,SY,Cell,Cell);
    DrawRect(FLinearColor(.2f,.31f,.33f,1.f),SX+2,SY+2,Cell-4,Cell-4);
    if(P->Inventory.IsValidIndex(Index)){
     const FNyItemStack& Stack=P->Inventory[Index];
     DrawText(ANyCharacter::GetItemName(Stack.Item),FLinearColor::White,SX+4,SY+11,nullptr,.66f);
     DrawText(FString::Printf(TEXT("x%d"),Stack.Quantity),FLinearColor(.5f,1.f,.8f),SX+5,SY+41,nullptr,.85f);
    }
   }
   DrawText(TEXT("RECIPES   [3] AXE: 3 WOOD + 2 STONE    [4] PICKAXE: 2 WOOD + 4 STONE"),FLinearColor(.75f,.86f,.88f),Left-14,Top+4*(Cell+Gap)+7,nullptr,.77f);
   DrawText(TEXT("I - CLOSE  |  E - HARVEST  |  F - EAT BERRIES"),FLinearColor(.55f,.7f,.74f),Left,Top+4*(Cell+Gap)+30,nullptr,.75f);
  }

  DrawText(FString::Printf(TEXT("PVP MELEE 20 DMG  |  DEATHS %d  |  %s"),P->DeathCount,P->bIsDead?TEXT("DEAD - RESPAWN IN 8 SEC"):TEXT("ALIVE")),P->bIsDead?FLinearColor::Red:FLinearColor::White,28,Y-170);
  DrawText(Info,FLinearColor(0.8f,0.98f,0.95f),28,Y-64,nullptr,1.25f);
  DrawText(FString::Printf(TEXT("HP  %.0f    HUNGER  %.0f    THIRST  %.0f    STAMINA  %.0f"),P->Health,P->Hunger,P->Thirst,P->Stamina),FLinearColor::White,28,Y-99);
 }
 if(const ANyWorldState* State=GetWorld()?GetWorld()->GetGameState<ANyWorldState>():nullptr){
  DrawText(FString::Printf(TEXT("TIME %02d:%02d  |  WEATHER %s  (%ds)"),FMath::FloorToInt(State->TimeOfDayHours),FMath::FloorToInt(FMath::Frac(State->TimeOfDayHours)*60.f),State->bRainActive?TEXT("RAIN / FOG"):TEXT("CLEAR"),State->WeatherSeconds),FLinearColor(.7f,.85f,1.f),28,119);
  DrawText(FString::Printf(TEXT("ECHO: %s  |  %ds"),State->bEchoActive?TEXT("ACTIVE"):TEXT("CALM"),State->EchoSeconds),State->bEchoActive?FLinearColor(1.f,.45f,.25f):FLinearColor(.2f,.85f,1.f),28,94);
 }
 DrawLine(X*.5f-9,Y*.5f,X*.5f+9,Y*.5f,FLinearColor::White,1.5f);
 DrawLine(X*.5f,Y*.5f-9,X*.5f,Y*.5f+9,FLinearColor::White,1.5f);
}
