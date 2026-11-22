#include "NyEnemy.h"
#include "NyCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "NavigationSystem.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "TimerManager.h"
#include "DrawDebugHelpers.h"
#include "AIController.h"
#include "Navigation/PathFollowingComponent.h"

ANyEnemy::ANyEnemy(){
 bReplicates=true;
 SetReplicateMovement(true);
 PrimaryActorTick.bCanEverTick=true;
 PrimaryActorTick.TickInterval=0.12f;
 GetCapsuleComponent()->InitCapsuleSize(40.f,76.f);
 GetCharacterMovement()->MaxWalkSpeed=230.f;
 // Visible prototype placeholder: capsule shape for gameplay testing.
 GetMesh()->SetVisibility(false);
 // Visible debug proxy: does not affect Character capsule movement/collision.
 DebugBody=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DebugBody"));
 DebugBody->SetupAttachment(GetCapsuleComponent());
 DebugBody->SetRelativeLocation(FVector(0.f,0.f,-4.f));
 DebugBody->SetRelativeScale3D(FVector(.65f,.65f,1.25f));
 DebugBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 static ConstructorHelpers::FObjectFinder<UStaticMesh> Proxy(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
 if(Proxy.Succeeded()) DebugBody->SetStaticMesh(Proxy.Object);
 AIControllerClass=AAIController::StaticClass();
 AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
}
void ANyEnemy::BeginPlay(){
 Super::BeginPlay();
 if(HasAuthority()){
  HomeLocation=GetActorLocation();PatrolPoint=HomeLocation;
  UNavigationSystemV1* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
  if(!Nav || !Nav->GetDefaultNavDataInstance(FNavigationSystem::DontCreate)){
   UE_LOG(LogTemp,Warning,TEXT("[NYVERRA 0.16] No navigation mesh. Add NavMeshBoundsVolume to a saved map and build paths; enemy will remain stationary until navigation becomes available."));
  }
 }
}
void ANyEnemy::Tick(float Dt){Super::Tick(Dt);if(HasAuthority()&&!bDead)Think();}
void ANyEnemy::MoveToward(const FVector& Destination){
 if(!HasAuthority()||bDead)return;
 // Do not issue unreachable MoveTo requests before the editor map has a usable navmesh.
 UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
 if(!Nav || !Nav->GetDefaultNavDataInstance(FNavigationSystem::DontCreate)) return;
 FNavLocation Reachable;
 if(!Nav->ProjectPointToNavigation(Destination, Reachable, FVector(350.f, 350.f, 500.f))) return;
 AAIController* AI=Cast<AAIController>(GetController());
 if(!AI)return;
 const float Now=GetWorld()->GetTimeSeconds();
 const bool bChanged=FVector::DistSquared2D(LastPathDestination,Reachable.Location)>FMath::Square(170.f);
 if(Now<NextPathRequestTime || (!bChanged && AI->GetMoveStatus()==EPathFollowingStatus::Moving))return;
 NextPathRequestTime=Now+0.65f;
 LastPathDestination=Reachable.Location;
 // Explicit pathfinding: requires a generated Recast NavMesh under the test territory.
 const EPathFollowingRequestResult::Type Result=AI->MoveToLocation(Reachable.Location,95.f,true,true,false,true,nullptr,true);
 if(Result==EPathFollowingRequestResult::Failed){
  NextPathRequestTime=Now+2.f; // Avoid spamming failed path requests.
 }
}
void ANyEnemy::Think(){
 UWorld* W=GetWorld();if(!W)return;
 const float Now=W->GetTimeSeconds();
 // Enemies remain near their original spawn to prevent endless pursuit.
 if(FVector::DistSquared2D(GetActorLocation(),HomeLocation)>FMath::Square(LeashRadius))Target.Reset();
 if(Now>=NextSearchTime || !Target.IsValid() || Target->bIsDead){
  NextSearchTime=Now+0.7f;
  Target.Reset();float BestSq=FMath::Square(AggroRadius);
  if(FVector::DistSquared2D(GetActorLocation(),HomeLocation)<FMath::Square(LeashRadius)){
   for(TActorIterator<ANyCharacter> It(W);It;++It){
    ANyCharacter* Candidate=*It;
    if(!IsValid(Candidate)||Candidate->bIsDead||Candidate->Health<=0.f)continue;
    const float D=FVector::DistSquared2D(GetActorLocation(),Candidate->GetActorLocation());
    if(D>=BestSq)continue;
    // Blocking cover should break visibility and prevent attacks through walls.
    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(NyEnemySight),false,this);
    Params.AddIgnoredActor(Candidate);
    const FVector Eye=GetActorLocation()+FVector(0,0,50.f);
    const FVector TargetEye=Candidate->GetActorLocation()+FVector(0,0,50.f);
    // Visibility must account for both static terrain and blocking dynamic base pieces.
    if(W->LineTraceSingleByChannel(Hit,Eye,TargetEye,ECC_Visibility,Params))continue;
    BestSq=D;Target=Candidate;
   }
  }
 }
 ANyCharacter* Victim=Target.Get();
 bAlerted=IsValid(Victim);
 if(!Victim){
  if(FVector::DistSquared2D(GetActorLocation(),HomeLocation)>FMath::Square(PatrolRadius)){
   MoveToward(HomeLocation);return;
  }
  if(Now>=NextPatrolChoice || FVector::DistSquared2D(GetActorLocation(),PatrolPoint)<FMath::Square(95.f)){
   NextPatrolChoice=Now+FMath::FRandRange(3.f,7.f);
   const FVector2D Offset=FMath::RandPointInCircle(PatrolRadius);
   const FVector Proposed=HomeLocation+FVector(Offset.X,Offset.Y,0.f);
   UNavigationSystemV1* Nav=FNavigationSystem::GetCurrent<UNavigationSystemV1>(W);
   FNavLocation ValidPoint;
   if(Nav && Nav->ProjectPointToNavigation(Proposed,ValidPoint,FVector(300.f,300.f,500.f))) PatrolPoint=ValidPoint.Location;
   else PatrolPoint=HomeLocation;
  }
  MoveToward(PatrolPoint);return;
 }
 const FVector Delta=Victim->GetActorLocation()-GetActorLocation();
 // Melee range must use full 3D distance. 2D range allowed attacks against
 // players far above/below the enemy on platforms or vertical terrain.
 const float Distance=Delta.Size();
 if(Distance>AttackRadius){MoveToward(Victim->GetActorLocation());return;}
 if(Now-LastAttackTime<1.5f || Victim->bIsDead)return;
 FCollisionQueryParams Sight(SCENE_QUERY_STAT(NyEnemyAttackSight),false,this);
 Sight.AddIgnoredActor(Victim);
 if(W->LineTraceTestByChannel(GetActorLocation()+FVector(0,0,50.f),Victim->GetActorLocation()+FVector(0,0,50.f),ECC_Visibility,Sight))return;
 LastAttackTime=Now;
 Victim->ReceiveCombatDamage(10.f,nullptr);
}
float ANyEnemy::TakeDamage(float Amount,const FDamageEvent& Event,AController* EventInstigator,AActor* Causer){
 if(!HasAuthority()||bDead||!FMath::IsFinite(Amount)||Amount<=0.f)return 0.f;
 const float Applied=FMath::Min(Health,Amount);
 Health=FMath::Max(0.f,Health-Amount);
 if(Health<=0.f){
  bDead=true;Target.Reset();bAlerted=false;
  OnRep_Dead();
  if(AAIController* AI=Cast<AAIController>(GetController())) AI->StopMovement();
  GetCharacterMovement()->DisableMovement();
  // Reward only the player who delivered the killing blow; never trust a client loot claim.
  ANyCharacter* Killer=Cast<ANyCharacter>(Causer);
  if(IsValid(Killer) && !Killer->bIsDead && FMath::FRand()<=FMath::Clamp(LootDropChance,0.f,1.f)){
   Killer->GiveLoot(ENyItemId::Berries,2);
  }
  // Reuse this replicated actor after a server-only cooldown. PvE must not
  // permanently disappear once players defeat the four initial enemies.
  GetWorldTimerManager().SetTimer(RespawnTimer,this,&ANyEnemy::RespawnEnemy,FMath::Max(10.f,RespawnSeconds),false);
 }
 ForceNetUpdate();return Applied;
}
void ANyEnemy::OnRep_Dead(){
 if(DebugBody) DebugBody->SetVisibility(!bDead,true);
 SetActorEnableCollision(!bDead);
}
void ANyEnemy::RespawnEnemy(){
 if(!HasAuthority() || !bDead)return;
 // Return to the original spawn instead of resurrecting in the middle of combat.
 SetActorLocation(HomeLocation,false,nullptr,ETeleportType::TeleportPhysics);
 Health=60.f;
 bDead=false;
 bAlerted=false;
 Target.Reset();
 NextSearchTime=GetWorld()->GetTimeSeconds()+1.f;
 NextPathRequestTime=0.f;
 LastPathDestination=FVector(1000000.f,1000000.f,1000000.f);
 GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 OnRep_Dead();
 ForceNetUpdate();
}
void ANyEnemy::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps)const{
 Super::GetLifetimeReplicatedProps(OutLifetimeProps);
 DOREPLIFETIME(ANyEnemy,Health);
 DOREPLIFETIME(ANyEnemy,bDead);
 DOREPLIFETIME(ANyEnemy,bAlerted);
}
