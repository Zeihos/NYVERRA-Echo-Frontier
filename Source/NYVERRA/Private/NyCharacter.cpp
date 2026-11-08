#include "NyCharacter.h"
#include "NyResource.h"
#include "NyLootCrate.h"
#include "NyEnemy.h"
#include "Kismet/GameplayStatics.h"
#include "NyBuildPiece.h"
#include "Engine/World.h"
#include "Engine/OverlapResult.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/InputComponent.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerStart.h"
#include "EngineUtils.h"
ANyCharacter::ANyCharacter(){
 bReplicates=true;PrimaryActorTick.bCanEverTick=true;
 GetCapsuleComponent()->InitCapsuleSize(42.f,92.f);
 Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
 Camera->SetupAttachment(GetCapsuleComponent());
 Camera->SetRelativeLocation(FVector(0,0,67));
 Camera->bUsePawnControlRotation=true;
 GetCharacterMovement()->MaxWalkSpeed=450.f;
 GetCharacterMovement()->JumpZVelocity=530.f;
 GetCharacterMovement()->AirControl=0.25f;
 bUseControllerRotationYaw=true;
}
void ANyCharacter::BeginPlay(){Super::BeginPlay();}
void ANyCharacter::SetupPlayerInputComponent(UInputComponent* Input){
 Super::SetupPlayerInputComponent(Input);
 Input->BindAxis(TEXT("MoveForward"),this,&ANyCharacter::Forward);
 Input->BindAxis(TEXT("MoveRight"),this,&ANyCharacter::Right);
 Input->BindAxis(TEXT("Turn"),this,&APawn::AddControllerYawInput);
 Input->BindAxis(TEXT("LookUp"),this,&APawn::AddControllerPitchInput);
 Input->BindAction(TEXT("Jump"),IE_Pressed,this,&ANyCharacter::TryJump);
 Input->BindAction(TEXT("Jump"),IE_Released,this,&ANyCharacter::StopJumpIfAlive);
 Input->BindAction(TEXT("Sprint"),IE_Pressed,this,&ANyCharacter::StartSprint);
 Input->BindAction(TEXT("Sprint"),IE_Released,this,&ANyCharacter::StopSprint);
 Input->BindAction(TEXT("Interact"),IE_Pressed,this,&ANyCharacter::Interact);
 Input->BindAction(TEXT("BuildFoundation"),IE_Pressed,this,&ANyCharacter::PlaceFoundation);
 Input->BindAction(TEXT("BuildWall"),IE_Pressed,this,&ANyCharacter::PlaceWall);
 Input->BindAction(TEXT("EatBerries"),IE_Pressed,this,&ANyCharacter::EatBerries);
 Input->BindAction(TEXT("DrinkWater"),IE_Pressed,this,&ANyCharacter::DrinkWater);
 Input->BindAction(TEXT("CraftAxe"),IE_Pressed,this,&ANyCharacter::CraftAxe);
 Input->BindAction(TEXT("CraftPickaxe"),IE_Pressed,this,&ANyCharacter::CraftPickaxe);
 Input->BindAction(TEXT("ToggleMouse"),IE_Pressed,this,&ANyCharacter::ToggleMouse);
 Input->BindAction(TEXT("Inventory"),IE_Pressed,this,&ANyCharacter::ToggleInventory);
 Input->BindAction(TEXT("MeleeAttack"),IE_Pressed,this,&ANyCharacter::MeleeAttack);
}
void ANyCharacter::TryJump(){if(!bIsDead && Health>0.f && !bInventoryOpen) Jump();}
void ANyCharacter::StopJumpIfAlive(){StopJumping();}
void ANyCharacter::Forward(float V){if(!bIsDead&&!bInventoryOpen&&Controller&&V!=0)AddMovementInput(GetActorForwardVector(),V);}
void ANyCharacter::Right(float V){if(!bIsDead&&!bInventoryOpen&&Controller&&V!=0)AddMovementInput(GetActorRightVector(),V);}
void ANyCharacter::StartSprint(){
 if(bIsDead||bInventoryOpen||Health<=0.f||Stamina<=5.f)return;
 bWantsSprint=true;OnRep_Sprint();ServerSetSprint(true);
}
void ANyCharacter::StopSprint(){
 bWantsSprint=false;OnRep_Sprint();ServerSetSprint(false);
}
void ANyCharacter::ToggleMouse(){
 if(bInventoryOpen)return; // Cursor state is owned by the open inventory.
 if(APlayerController* PC=Cast<APlayerController>(GetController())){
  bMouseFree=!bMouseFree;
  PC->bShowMouseCursor=bMouseFree;
  if(bMouseFree) PC->SetInputMode(FInputModeGameAndUI());
  else PC->SetInputMode(FInputModeGameOnly());
 }
}
FString ANyCharacter::GetItemName(ENyItemId Item){
 switch(Item){
 case ENyItemId::Wood: return TEXT("WOOD");
 case ENyItemId::Stone: return TEXT("STONE");
 case ENyItemId::EchoShard: return TEXT("ECHO SHARD");
 case ENyItemId::Berries: return TEXT("BERRIES");
 case ENyItemId::Water: return TEXT("CLEAN WATER");
 case ENyItemId::Axe: return TEXT("STONE AXE");
 case ENyItemId::Pickaxe: return TEXT("STONE PICKAXE");
 default: return TEXT("UNKNOWN");
 }
}
void ANyCharacter::ToggleInventory(){
 bInventoryOpen=!bInventoryOpen;
 if(bInventoryOpen){StopJumping();StopSprint();}
 if(APlayerController* PC=Cast<APlayerController>(GetController())){
  PC->bShowMouseCursor=bInventoryOpen;
  bMouseFree=bInventoryOpen;
  if(bInventoryOpen)PC->SetInputMode(FInputModeGameAndUI());
  else PC->SetInputMode(FInputModeGameOnly());
 }
}
void ANyCharacter::OnRep_Sprint(){
 GetCharacterMovement()->MaxWalkSpeed=bWantsSprint?700.f:450.f;
}
void ANyCharacter::ServerSetSprint_Implementation(bool bSprinting){
 if(!HasAuthority())return;
 bWantsSprint=bSprinting&&!bIsDead&&Health>0.f&&Stamina>5.f;
 OnRep_Sprint();ForceNetUpdate();
}
void ANyCharacter::Interact(){if(!bIsDead&&!bInventoryOpen) ServerInteract();}
void ANyCharacter::MeleeAttack(){if(!bIsDead&&!bInventoryOpen) ServerMeleeAttack();}
void ANyCharacter::ServerMeleeAttack_Implementation(){
 if(!HasAuthority()||bIsDead||Health<=0.f||!Controller)return;
 const float Now=GetWorld()->GetTimeSeconds();
 if(Now-LastAttackTime<0.75f)return;
 LastAttackTime=Now;
 const FVector Eye = GetPawnViewLocation();
 if (FVector::DistSquared(Eye, GetActorLocation()) > FMath::Square(220.f)) return;
 const FRotator Aim = Controller->GetControlRotation();
 FHitResult Hit;
 FCollisionQueryParams Params(SCENE_QUERY_STAT(NyMelee),false,this);
 const FVector End=Eye+Aim.Vector()*190.f;
 if(!GetWorld()->LineTraceSingleByChannel(Hit,Eye,End,ECC_Visibility,Params))return;
 if(ANyEnemy* Enemy=Cast<ANyEnemy>(Hit.GetActor())){
  if(!Enemy->bDead && FVector::DistSquared(GetActorLocation(),Enemy->GetActorLocation())<=FMath::Square(245.f))
   UGameplayStatics::ApplyDamage(Enemy,20.f,Controller,this,nullptr);
  return;
 }
 ANyCharacter* Victim=Cast<ANyCharacter>(Hit.GetActor());
 if(!Victim||Victim==this||Victim->bIsDead||FVector::DistSquared(GetActorLocation(),Victim->GetActorLocation())>FMath::Square(245.f))return;
 Victim->ReceiveCombatDamage(20.f,this);
}
void ANyCharacter::ReceiveCombatDamage(float Amount,ANyCharacter* Attacker){
 if(!HasAuthority()||bIsDead||!FMath::IsFinite(Amount)||Amount<=0.f)return;
 Health=FMath::Max(0.f,Health-FMath::Min(Amount,100.f));
 if(Health>0.f)return;
 bIsDead=true; DeathCount++;
 bWantsSprint=false;OnRep_Sprint();
 GetCharacterMovement()->StopMovementImmediately();
 GetCharacterMovement()->DisableMovement();
 GetWorldTimerManager().SetTimer(RespawnTimer,this,&ANyCharacter::RespawnAfterDeath,8.f,false);
 ForceNetUpdate();
}
void ANyCharacter::RespawnAfterDeath(){
 if(!HasAuthority()||!bIsDead)return;
 // Spawn in a known safe center for this prototype; a real spawn manager comes later.
 // Place respawning players above the authoritative collision surface (Landscape or test ground).
 // Never use a fixed Z: it can trap players below terrain after importing a heightmap.
 // Use a map-authored PlayerStart when possible; avoid respawning everyone at world origin.
 FVector RespawnLocation(0.f,0.f,180.f);
 // Multiplayer spawn safety: choose the PlayerStart with the greatest minimum
 // distance to living players instead of repeatedly using the first spawn.
 float BestClearanceSquared=-1.f;
 for(TActorIterator<APlayerStart> It(GetWorld());It;++It){
  if(!IsValid(*It))continue;
  const FVector Candidate=It->GetActorLocation();
  float NearestPlayerSquared=FMath::Square(100000.f);
  for(TActorIterator<ANyCharacter> PlayerIt(GetWorld());PlayerIt;++PlayerIt){
   const ANyCharacter* Other=*PlayerIt;
   if(!IsValid(Other)||Other==this||Other->bIsDead)continue;
   NearestPlayerSquared=FMath::Min(NearestPlayerSquared,
    FVector::DistSquared2D(Candidate,Other->GetActorLocation()));
  }
  if(NearestPlayerSquared>BestClearanceSquared){
   BestClearanceSquared=NearestPlayerSquared;
   RespawnLocation=Candidate;
  }
 }
 // Trace through overhanging site geometry rather than placing the player on a roof.
 FHitResult GroundHit;
 FCollisionQueryParams GroundQuery(SCENE_QUERY_STAT(NyRespawnGround), false, this);
 bool bFoundGround = false;
 const FVector GroundStart(RespawnLocation.X, RespawnLocation.Y, 50000.f);
 const FVector GroundEnd(RespawnLocation.X, RespawnLocation.Y, -50000.f);
 for (int32 Attempt = 0; Attempt < 64; ++Attempt)
 {
  if (!GetWorld()->LineTraceSingleByChannel(GroundHit, GroundStart, GroundEnd, ECC_Visibility, GroundQuery)) break;
  AActor* Surface = GroundHit.GetActor();
  if (IsValid(Surface) && (Surface->ActorHasTag(TEXT("NYVERRA_SiteGeometry")) ||
      Surface->IsA<ANyBuildPiece>() || Surface->IsA<ANyResource>() ||
      Surface->IsA<ANyLootCrate>() || Surface->IsA<APawn>()))
  {
   GroundQuery.AddIgnoredActor(Surface);
   continue;
  }
  if (GroundHit.ImpactNormal.Z >= 0.7f)
  {
   RespawnLocation.Z = GroundHit.ImpactPoint.Z + GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 30.f;
   bFoundGround = true;
  }
  break;
 }
 if (!bFoundGround)
 {
  UE_LOG(LogTemp, Warning, TEXT("[NYVERRA] Respawn: no suitable floor under PlayerStart; keeping authored spawn elevation"));
 }
 SetActorLocation(RespawnLocation,false,nullptr,ETeleportType::TeleportPhysics);
 Inventory.Reset();RefreshLegacyCounters();
 Health=100.f;Hunger=100.f;Thirst=100.f;Stamina=100.f;
 bIsDead=false;bWantsSprint=false;OnRep_Sprint();
 GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 GetCharacterMovement()->MaxWalkSpeed=450.f;
 ForceNetUpdate();
}
void ANyCharacter::PlaceFoundation(){if(!bInventoryOpen&&!bIsDead)ServerPlacePiece(0);}
void ANyCharacter::PlaceWall(){if(!bInventoryOpen&&!bIsDead)ServerPlacePiece(1);}
void ANyCharacter::EatBerries(){if(!bIsDead&&!bInventoryOpen)ServerEatBerries();}
void ANyCharacter::DrinkWater(){if(!bIsDead&&!bInventoryOpen)ServerDrinkWater();}
void ANyCharacter::CraftAxe(){if(!bInventoryOpen&&!bIsDead)ServerCraft(0);}
void ANyCharacter::CraftPickaxe(){if(!bInventoryOpen&&!bIsDead)ServerCraft(1);}
bool ANyCharacter::GiveLoot(ENyItemId Item,int32 Quantity){return HasAuthority()&&AddItem(Item,Quantity);}
int32 ANyCharacter::CountItem(ENyItemId Item) const {
 int32 Total=0; for(const FNyItemStack& Stack: Inventory) if(Stack.Item==Item) Total+=Stack.Quantity;
 return Total;
}
void ANyCharacter::RefreshLegacyCounters(){
 Wood=CountItem(ENyItemId::Wood); Stone=CountItem(ENyItemId::Stone);
 Echo=CountItem(ENyItemId::EchoShard); Berries=CountItem(ENyItemId::Berries);
 ForceNetUpdate();
}
bool ANyCharacter::AddItem(ENyItemId Item,int32 Quantity){
 if(!HasAuthority()||Quantity<=0)return false;
 const int32 MaxStack=(Item==ENyItemId::Axe||Item==ENyItemId::Pickaxe)?1:100;
 int32 Space=0;
 for(const FNyItemStack& Stack:Inventory) if(Stack.Item==Item) Space+=MaxStack-Stack.Quantity;
 Space+=(MaxSlots-Inventory.Num())*MaxStack;
 if(Space<Quantity)return false; // atomic: no partially added harvests
 for(FNyItemStack& Stack:Inventory){
  if(Stack.Item!=Item||Stack.Quantity>=MaxStack)continue;
  const int32 N=FMath::Min(Quantity,MaxStack-Stack.Quantity);Stack.Quantity+=N;Quantity-=N;
  if(Quantity==0){RefreshLegacyCounters();return true;}
 }
 while(Quantity>0){
  FNyItemStack Stack;Stack.Item=Item;Stack.Quantity=FMath::Min(MaxStack,Quantity);
  Inventory.Add(Stack);Quantity-=Stack.Quantity;
 }
 RefreshLegacyCounters();return true;
}
bool ANyCharacter::SpendItems(ENyItemId A,int32 ACount,ENyItemId B,int32 BCount){
 if(!HasAuthority()||ACount<0||BCount<0)return false;
 if(A==B){if(CountItem(A)<ACount+BCount)return false;}
 else if(CountItem(A)<ACount||CountItem(B)<BCount)return false;
 auto Remove=[this](ENyItemId Kind,int32 Amount){
  for(int32 i=Inventory.Num()-1;i>=0&&Amount>0;--i){
   if(Inventory[i].Item!=Kind)continue;
   const int32 Used=FMath::Min(Amount,Inventory[i].Quantity);
   Inventory[i].Quantity-=Used;Amount-=Used;
   if(Inventory[i].Quantity==0)Inventory.RemoveAt(i);
  }
 };
 Remove(A,ACount);Remove(B,BCount);RefreshLegacyCounters();return true;
}
void ANyCharacter::ServerCraft_Implementation(uint8 RecipeId){
 if(Health<=0.f||bIsDead)return;
 if(!HasAuthority()||RecipeId>1)return;
 const ENyItemId Result=RecipeId==0?ENyItemId::Axe:ENyItemId::Pickaxe;
 const int32 WoodCost=RecipeId==0?3:2;
 const int32 StoneCost=RecipeId==0?2:4;
 if(CountItem(ENyItemId::Wood)<WoodCost||CountItem(ENyItemId::Stone)<StoneCost)return;
 // Simulate ingredient consumption in a temporary inventory before changing server state.
 // This correctly handles split stacks and a completely full inventory.
 TArray<FNyItemStack> Preview = Inventory;
 auto PreviewRemove = [&Preview](ENyItemId Kind, int32 Amount)
 {
  for (int32 Index = Preview.Num() - 1; Index >= 0 && Amount > 0; --Index)
  {
   if (Preview[Index].Item != Kind) continue;
   const int32 Used = FMath::Min(Amount, Preview[Index].Quantity);
   Preview[Index].Quantity -= Used;
   Amount -= Used;
   if (Preview[Index].Quantity == 0) Preview.RemoveAt(Index);
  }
 };
 PreviewRemove(ENyItemId::Wood, WoodCost);
 PreviewRemove(ENyItemId::Stone, StoneCost);
 if (Preview.Num() >= MaxSlots) return; // tools always require a new single-item stack
 if (!SpendItems(ENyItemId::Wood, WoodCost, ENyItemId::Stone, StoneCost)) return;
 // Capacity was checked using the exact post-consumption state.
 if (!AddItem(Result, 1))
 {
  UE_LOG(LogTemp, Error, TEXT("[NYVERRA] Craft inventory invariant failed"));
  AddItem(ENyItemId::Wood, WoodCost);
  AddItem(ENyItemId::Stone, StoneCost);
 }

}
void ANyCharacter::ServerEatBerries_Implementation(){
 if(Health<=0.f||bIsDead)return;
 if(!HasAuthority()||CountItem(ENyItemId::Berries)<=0||Hunger>=100.f)return;
 if(SpendItems(ENyItemId::Berries,1,ENyItemId::Wood,0))Hunger=FMath::Min(100.f,Hunger+18.f);
}
// Water is consumed only from the server-owned inventory: no client-provided
// quantity/target, no refill while dead, and no free rehydration at full thirst.
void ANyCharacter::ServerDrinkWater_Implementation(){
 if(!HasAuthority()||bIsDead||Health<=0.f||Thirst>=100.f)return;
 const float Now=GetWorld()->GetTimeSeconds();
 if(Now-LastDrinkTime<0.6f||CountItem(ENyItemId::Water)<1)return;
 if(SpendItems(ENyItemId::Water,1,ENyItemId::Wood,0)){
  LastDrinkTime=Now;
  Thirst=FMath::Min(100.f,Thirst+35.f);
  ForceNetUpdate();
 }
}
void ANyCharacter::Tick(float DT){
 Super::Tick(DT);if(!HasAuthority()||bIsDead)return;
 const bool bMoving=GetVelocity().SizeSquared2D()>10000.f;
 if(bWantsSprint && bMoving && Stamina>0.f){Stamina=FMath::Max(0.f,Stamina-12.f*DT);}
 else {Stamina=FMath::Min(100.f,Stamina+8.f*DT);}
 if(Stamina<=0.f&&bWantsSprint){bWantsSprint=false;OnRep_Sprint();ForceNetUpdate();}
 SurvivalAccumulator+=DT;
 while(SurvivalAccumulator>=10.f){SurvivalAccumulator-=10.f;
 Hunger=FMath::Max(0.f,Hunger-1.f);Thirst=FMath::Max(0.f,Thirst-1.5f);
 if((Hunger<=0.f||Thirst<=0.f)&&!bIsDead)ReceiveCombatDamage(2.f,nullptr);
 }
}
void ANyCharacter::ServerPlacePiece_Implementation(uint8 Type){
 if(Health<=0.f||bIsDead)return;
 if(!HasAuthority()||Type>1||CountItem(ENyItemId::Wood)<4||CountItem(ENyItemId::Stone)<2)return;
 // Reject rapid build RPC spam on the dedicated server.
 const float Now = GetWorld()->GetTimeSeconds();
 if (Now - LastBuildTime < 0.35f) return;
 const FVector Forward2D=GetActorForwardVector().GetSafeNormal2D();
 FVector P=GetActorLocation()+Forward2D*260.f;
 P.X=FMath::GridSnap(P.X,300.f);P.Y=FMath::GridSnap(P.Y,300.f);
 // The prototype's authoritative resource/spawn region is bounded.
 if (FMath::Abs(P.X)>4350.f || FMath::Abs(P.Y)>4350.f) return; // Full 300 cm footprint must remain inside the map.
 // Resolve the authoritative terrain height instead of placing every structure at Z=0.
 FHitResult GroundHit;
 FCollisionQueryParams GroundParams(SCENE_QUERY_STAT(NyBuildingGround), false, this);
 const FVector GroundStart(P.X, P.Y, 50000.f);
 const FVector GroundEnd(P.X, P.Y, -50000.f);
 // Ignore decorative site geometry: a roof is not a valid terrain placement surface.
 bool bFoundTerrain = false;
 for (int32 Attempt = 0; Attempt < 64; ++Attempt) {
  if (!GetWorld()->LineTraceSingleByChannel(GroundHit, GroundStart, GroundEnd, ECC_Visibility, GroundParams)) break;
  AActor* HitActor = GroundHit.GetActor();
  if (IsValid(HitActor) && HitActor->ActorHasTag(TEXT("NYVERRA_SiteGeometry"))) {
   GroundParams.AddIgnoredActor(HitActor);
   continue;
  }
  bFoundTerrain = true;
  break;
 }
 if (!bFoundTerrain) return;
 // Walls may attach to the top edge of a foundation, but foundations
 // cannot stack, and no structure may be built on top of an existing wall.
 ANyBuildPiece* Foundation=Cast<ANyBuildPiece>(GroundHit.GetActor());
 if(Foundation && (Type!=1 || Foundation->PieceType!=0))return;
 if(GroundHit.ImpactNormal.Z<0.85f || !GroundHit.GetComponent())return;
 // Authoritative foundations are explicit valid supports even if their
 // runtime-spawned mesh component reports Movable on this engine version.
 if(!Foundation && GroundHit.GetComponent()->Mobility!=EComponentMobility::Static)return;
 // 240 cm wall length + 30 cm thickness allows neighboring perpendicular
 // walls to meet at corners without collider overlap. Foundation is 300x300.
 const FVector Extent=Type==0?FVector(150.f,150.f,15.f):FVector(120.f,15.f,125.f);
 FRotator Rot=Type==0?FRotator::ZeroRotator:FRotator(0.f,FMath::GridSnap(GetActorRotation().Yaw,90.f),0.f);
 P.Z=GroundHit.ImpactPoint.Z+Extent.Z;
 if(Type==1 && Foundation){
  // The closest side to the player selects one of four foundation edges.
  // Geometry and collision are calculated ONLY from server-owned actors.
  const FVector Delta=GetActorLocation()-Foundation->GetActorLocation();
  if(Delta.SizeSquared2D()>FMath::Square(470.f))return;
  const bool bEastWest=FMath::Abs(Delta.X)>FMath::Abs(Delta.Y);
  const float Side=(bEastWest?Delta.X:Delta.Y)>=0.f?1.f:-1.f;
  Rot=bEastWest?FRotator(0.f,90.f,0.f):FRotator::ZeroRotator;
  P=Foundation->GetActorLocation()+
    (bEastWest?FVector(135.f*Side,0.f,0.f):FVector(0.f,135.f*Side,0.f));
  P.Z=Foundation->GetActorLocation().Z+15.f+Extent.Z;
 }

 // Check all collidable buildables, pawns, resources and loot crates.
 // Unlike the old zero-length sweep, this check respects the wall rotation.
 FCollisionObjectQueryParams ObjectTypes;
 ObjectTypes.AddObjectTypesToQuery(ECC_WorldStatic);
 ObjectTypes.AddObjectTypesToQuery(ECC_WorldDynamic);
 ObjectTypes.AddObjectTypesToQuery(ECC_Pawn);
 FCollisionQueryParams Query(SCENE_QUERY_STAT(NyBuildOverlap), false, this);
 TArray<FOverlapResult> Overlaps;
 GetWorld()->OverlapMultiByObjectType(Overlaps, P, Rot.Quaternion(), ObjectTypes, FCollisionShape::MakeBox(Extent * 0.96f), Query);
 for (const FOverlapResult& Overlap : Overlaps) {
  AActor* Other = Overlap.GetActor();
  if (!Other || Other == GroundHit.GetActor()) continue;
  // Fail closed: any blocking actor (including untagged level meshes) prevents placement.
  // The terrain below the footprint is the only allowed blocking overlap.
  if (UPrimitiveComponent* OtherComponent = Overlap.GetComponent()) {
   if (OtherComponent->GetCollisionEnabled() != ECollisionEnabled::NoCollision &&
       OtherComponent->GetCollisionResponseToChannel(ECC_WorldDynamic) == ECR_Block) return;
  }
  if (Other->ActorHasTag(TEXT("NYVERRA_SiteGeometry")) || Other->IsA<ANyBuildPiece>() || Other->IsA<APawn>() || Other->IsA<ANyResource>() || Other->IsA<ANyLootCrate>() || Other->IsA<ANyEnemy>()) return;
 }
 if(ANyBuildPiece* Piece=GetWorld()->SpawnActor<ANyBuildPiece>(P,Rot)){
  // If the item transaction is rejected, remove the spawned piece.
  if (!SpendItems(ENyItemId::Wood,4,ENyItemId::Stone,2)) { Piece->Destroy(); return; }
  Piece->Initialize(Type);
  LastBuildTime = Now; // Only successful placements trigger the build cooldown.
 }
}

void ANyCharacter::ServerInteract_Implementation(){
 if(Health<=0.f||bIsDead)return;
 if(!Controller||!HasAuthority())return;
 const float Now=GetWorld()->GetTimeSeconds();if(Now-LastInteractionTime<0.3f)return;LastInteractionTime=Now;
 const FVector Eye = GetPawnViewLocation();
 if (FVector::DistSquared(Eye, GetActorLocation()) > FMath::Square(220.f)) return;
 const FRotator Aim = Controller->GetControlRotation();
 FHitResult Hit;
 FCollisionQueryParams Params(SCENE_QUERY_STAT(NyHarvest),false,this);
 const FVector End=Eye+Aim.Vector()*420.f;
 if(!GetWorld()->LineTraceSingleByChannel(Hit,Eye,End,ECC_Visibility,Params))return;
 if (ANyLootCrate* Crate = Cast<ANyLootCrate>(Hit.GetActor())) {
  if (FVector::DistSquared(GetActorLocation(), Crate->GetActorLocation()) > FMath::Square(500.f)) return;
  Crate->TryLoot(this);
  return;
 }
 ANyResource* Resource=Cast<ANyResource>(Hit.GetActor());
 if(!Resource||FVector::Dist(GetActorLocation(),Resource->GetActorLocation())>500.f)return;
 const ENyResourceKind Kind=Resource->Kind;
 const ENyItemId Item=Kind==ENyResourceKind::Wood?ENyItemId::Wood:
  Kind==ENyResourceKind::Stone?ENyItemId::Stone:
  Kind==ENyResourceKind::Berries?ENyItemId::Berries:
  Kind==ENyResourceKind::Water?ENyItemId::Water:ENyItemId::EchoShard;
 const int32 Award=(Item==ENyItemId::Wood&&CountItem(ENyItemId::Axe)>0)||
   (Item==ENyItemId::Stone&&CountItem(ENyItemId::Pickaxe)>0)?2:1;
 // Harvest the authoritative node first, then credit the exact returned amount.
 // AddItem is atomic on capacity; the preflight check prevents consuming a node
 // when the inventory is full, including split stacks and tools.
 const int32 MaxStack = 100;
 int32 Capacity = (MaxSlots - Inventory.Num()) * MaxStack;
 for (const FNyItemStack& Stack : Inventory)
  if (Stack.Item == Item) Capacity += FMath::Max(0, MaxStack - Stack.Quantity);
 // A tool can collect two units, but one remaining unit must still be harvestable.
 const int32 Requested=FMath::Min(Award,Resource->Remaining);
 if(Requested<=0 || Capacity<Requested)return;
 int32 Harvested = 0;
 if (!Resource->Harvest(Harvested, Requested) || Harvested <= 0) return;
 if (!AddItem(Item, Harvested))
  UE_LOG(LogTemp, Error, TEXT("[NYVERRA] Inventory credit failed after harvest; verify resource transaction"));
}
void ANyCharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyCharacter,bWantsSprint);
 DOREPLIFETIME(ANyCharacter,bIsDead);DOREPLIFETIME(ANyCharacter,DeathCount);
 DOREPLIFETIME(ANyCharacter,Inventory);DOREPLIFETIME(ANyCharacter,Health);DOREPLIFETIME(ANyCharacter,Hunger);
 DOREPLIFETIME(ANyCharacter,Wood);DOREPLIFETIME(ANyCharacter,Stone);DOREPLIFETIME(ANyCharacter,Echo);
 DOREPLIFETIME(ANyCharacter,Berries);DOREPLIFETIME(ANyCharacter,Thirst);DOREPLIFETIME(ANyCharacter,Stamina);
}
