#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "NyHUD.generated.h"
UCLASS()
class NYVERRA_API ANyHUD : public AHUD {
 GENERATED_BODY()
public:
 virtual void DrawHUD() override;
};
