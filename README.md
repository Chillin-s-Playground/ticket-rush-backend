# Ticket Rush
<div>
  <img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/redis-FF4438?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/websocket-C93CD7?style=for-the-badge&logo=socket&logoColor=white" />
  <img src="https://img.shields.io/badge/amazon_aws-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" />
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

1. **대기열 & 혼잡 제어**
    - Redis LIST로 대기열 관리, 입장 토큰 기반 요청 게이팅
2. **좌석 홀드 & TTL**
    - Redis `SET NX PX`로 원자적 홀드(60초 TTL)
    - TTL 만료 시 자동 해제, 실시간 좌석 상태 브로드캐스트
3. **결제 확정 & 데이터 일관성**
    - PostgreSQL 트랜잭션 + `(event_id, seat_id)` UNIQUE 제약
    - 결제 시 홀드 소유자 검증 → 확정 → 다른 유저 중복 예약 차단
4. **실시간 UI 반영**
    - WebSocket으로 좌석 상태(available/held/sold) 업데이트
    - 1~2초 내 전파 보장

## 3. 성과 & 배운 점

- Redis `SET NX EX`를 이용한 **원자적 좌석 점유**로 고부하 경쟁 상황에서도 단일 점유 보장
- DB 유니크 제약 + 트랜잭션으로 **중복 결제 방지** 및 **멱등성(Idempotent) 결제 API** 구현
- WebSocket 브로드캐스트 + 다건 payload 패치로 **수천 석 UI 동기화 성능 최적화**
- Presence/Active 관리와 TTL 만료 정책으로 **이탈/만료 정리의 일관성**과 **운영 안정성** 확보

## 4. 보완 예정 (Next Step)

- [ ] mermaid 다이어그램 추가 (FastAPI ↔ Redis ↔ DB ↔ WS)
- [ ] 부하 테스트 결과 요약 (동시성, 브로드캐스트 지연 시간)
- [ ] 만료 브로드캐스트 전략 명시 (키스페이스 노티 or 주기 클린업)
- [ ] 에러 코드 정책 표 정리 및 링크화
- [ ] 간단 e2e 테스트 시나리오 문서화
