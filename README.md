# Ticket Rush
<div>
  <img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/redis-FF4438?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/socket-C93CD7?style=for-the-badge&logo=socket&logoColor=white" />
  <img src="https://img.shields.io/badge/aws-FF9900?style=for-the-badge&logo=aws&logoColor=white" />
</div>

## 1. 프로젝트 설명
FastAPI + Redis + RDBMS(SQLAlchemy)를 활용해 실시간 좌석상태 동기화와 안전한 결제가 가능한 **대규모 티켓 예매 서비스**를 구현했습니다. (본 레포지터리는 백엔드 영역만 다룹니다. )

```text
  1. 실시간 좌석 상태 반영
   - WebSocket 브로드캐스트를 통해 좌석 상태(HOLD, SOLD, AVAILABLE)가 즉시 모든 사용자에게 반영됩니다.
   - 서버에서 다건 상태 변경을 payload로 묶어서 push하면, 클라이언트는 일괄 갱신을 합니다.

  2. 원자적 좌석 HOLD
     - Redis `SET NX EX` 명령을 사용해 동일 좌석을 동시에 두 명 이상이 점유하지 못하도록 보장합니다.
     - TTL을 걸어 일정 시간이 지나면 자동으로 HOLD가 해제되어 다른 사용자가 선택할 수 있습니다.
  
  3. 트랜잭션 기반 결제 확정
     - DB 트랜잭션과 유니크 제약을 통해 이미 결제된 좌석은 중복으로 구매할 수 없습니다.
     - 결제 완료 시 HOLD 키는 제거되고 SOLD 상태가 실시간으로 브로드캐스트됩니다.
  
  4. Presence / Active 관리
     - 사용자가 페이지를 이탈하거나 세션이 만료되면 활성 유저 집합에서 제거됩니다.
     - Redis를 활용해 이벤트 단위 활성 유저를 관리하고, TTL 기반 보조키로 안정적인 만료 처리를 보장합니다.
```

## 2. 핵심 구현 포인트 (Technical Highlights)

### 1 좌석 HOLD – 단일 점유(1석-1유저) 보장
- Redis **문자열 키**로 좌석 당 소유자(`user_uuid`)를 저장
  - `SET key value NX EX ttl`
- 이미 점유된 좌석일 경우 **409 Conflict** 반환
- TTL로 자연 만료되며, 만료/취소 시 AVAILABLE 브로드캐스트
  #### 핵심 코드 스니펫
  
  ```python
    # 좌석 당 소유자(`user_uuid`)를 저장
   await self.redis.set(
        f"hold:{event_id}:{seat_label}",
        user_uuid,
        nx=True,        # 이미 존재하면 실패
        ex=HOLD_EXPIRE  # TTL 설정
    )
  
    # 이미 점유된 좌석일 경우 409 Conflict 반환
    if not locked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 선택된 좌석입니다.",
        )
  
    # TTL 만료/취소 시 AVAILABLE 브로드캐스트
    await ticket_repo.del_hold_the_seat(event_id=event_id, seat_label=seat_label)
    payload = [{"seat_id": seat_id, "seat_status": "AVAILABLE"}]
    
    await self.manager.broadcast(
        room_id=f"event:{event_id}:seat_update",
        message={"type": "seat_update", "payload": payload},
    )
  
  ```

---

### 2 결제 확정 – DB 트랜잭션 + 보상
- 결제 시도 시 내가 HOLD 중인지 검증 → 아니면 409 Error
- 좌석 행에 대한 **유니크 제약**으로 중복 구매 차단 → 403 Forbidden
- 성공 시 HOLD 키 제거 + SOLD 브로드캐스트


  #### 핵심 코드 스니펫
  ```python
  # 이미 SOLD 여부 체크
  is_sold = await ticket_repo.is_exist_sold_seat(seat_id=seat_id)
  if is_sold:
      raise HTTPException(
          status_code=409,
          detail="이미 결제가 완료된 좌석입니다."
      )
  
  # HOLD 여부 및 소유자 검증
  is_hold = await ticket_repo.is_exist_hold_seat(event_id=event_id, seat_label=seat_label)
  if not is_hold or is_hold != user_uuid:
      raise HTTPException(
          status_code=409,
          detail="이미 다른 사용자가 선택한 좌석입니다."
      )
  
  # 결제 처리 & SOLD 브로드캐스트
  await ticket_repo.set_sold_seat(user_uuid=user_uuid, seat_id=seat_id)
  await ticket_repo.del_hold_the_seat(event_id=event_id, seat_label=seat_label)
  await self.manager.broadcast(
      room_id=f"event:{event_id}:seat_update",
      message={"type": "seat_update", "payload": {"seat_id": seat_id, "seat_status": "SOLD"}},
  )
```
