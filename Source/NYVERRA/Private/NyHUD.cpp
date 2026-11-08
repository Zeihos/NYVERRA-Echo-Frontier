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
 DrawText(TEXT("NYVERRA / ECHO FRONTIER  -  DEVELOPMENT BUILD"),FLinearColor(0.1f,0.9f,0.9f),28,24,nullptr,1.1f);
 // Two short control rows stay readable on typical 1366px and 1920px screens.
 DrawText(TEXT("WASD MOVE  |  MOUSE LOOK  |  SPACE JUMP  |  SHIFT SPRINT  |  LMB ATTACK  |  E GATHER  |  I INVENTORY"),FLinearColor::White,28,56,nullptr,0.9f);
 DrawText(TEXT("1 FOUNDATION  |  2 WALL  |  3 AXE  |  4 PICKAXE  |  F EAT  |  Q DRINK  |  TAB CURSOR"),FLinearColor(.77f,.87f,.91f),28,78,nullptr,0.9f);
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
  // Responsive, low-cost Canvas status bars in place of an unreadable number row.
  // These bars do not rely on imported textures or UMG assets.
  const float VitalBarW=146.f;
  const float VitalGap=20.f;
  auto DrawVital=[&](const TCHAR* Label,float Value,const FLinearColor& Color,int32 Index){
   const float SX=28.f+Index*(VitalBarW+VitalGap);
   const float SY=Y-112.f;
   const float Level=FMath::Clamp(Value/100.f,0.f,1.f);
   DrawText(FString::Printf(TEXT("%s  %.0f"),Label,Value),FLinearColor(.84f,.9f,.94f),SX,SY,nullptr,.92f);
   DrawRect(FLinearColor(.055f,.08f,.105f,.94f),SX,SY+25.f,VitalBarW,9.f);
   DrawRect(Color,SX+1.f,SY+26.f,FMath::Max(0.f,(VitalBarW-2.f)*Level),7.f);
  };
  DrawVital(TEXT("HEALTH"),P->Health,FLinearColor(.93f,.28f,.32f),0);
  DrawVital(TEXT("HUNGER"),P->Hunger,FLinearColor(.91f,.64f,.23f),1);
  DrawVital(TEXT("THIRST"),P->Thirst,FLinearColor(.29f,.72f,.94f),2);
  DrawVital(TEXT("STAMINA"),P->Stamina,FLinearColor(.34f,.85f,.67f),3);
 }
 if(const ANyWorldState* State=GetWorld()?GetWorld()->GetGameState<ANyWorldState>():nullptr){
  DrawText(FString::Printf(TEXT("TIME %02d:%02d  |  WEATHER %s  (%ds)"),FMath::FloorToInt(State->TimeOfDayHours),FMath::FloorToInt(FMath::Frac(State->TimeOfDayHours)*60.f),State->bRainActive?TEXT("RAIN / FOG"):TEXT("CLEAR"),State->WeatherSeconds),FLinearColor(.7f,.85f,1.f),28,150);
  DrawText(FString::Printf(TEXT("ECHO: %s  |  %ds"),State->bEchoActive?TEXT("ACTIVE"):TEXT("CALM"),State->EchoSeconds),State->bEchoActive?FLinearColor(1.f,.45f,.25f):FLinearColor(.2f,.85f,1.f),28,123);
 }
 // Don't draw a combat reticle over the open inventory panel.
 const ANyCharacter* LocalPawn=Cast<ANyCharacter>(GetOwningPawn());
 if(!LocalPawn || !LocalPawn->bInventoryOpen){
  DrawLine(X*.5f-9,Y*.5f,X*.5f+9,Y*.5f,FLinearColor::White,1.5f);
  DrawLine(X*.5f,Y*.5f-9,X*.5f,Y*.5f+9,FLinearColor::White,1.5f);
 }
}
