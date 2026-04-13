# 시스템 아키텍처 문서

## 1. 시스템 개요

사내 주문관리 플랫폼 "OrderFlow"는 마이크로서비스 아키텍처(MSA)로 구성되어 있다.
일 평균 주문 처리량 50만 건, 피크 시 초당 1,200 TPS를 처리한다.

## 2. 서비스 구성

### 2.1 핵심 서비스

| 서비스 | 포트 | 기술 스택 | 역할 | SLA |
|--------|------|----------|------|-----|
| order-api | 8080 | Java 21 + Spring Boot 3.2 | 주문 CRUD + 상태 관리 | 99.95% |
| payment-service | 8081 | Java 21 + Spring Boot 3.2 | 결제 처리 + PG 연동 | 99.99% |
| inventory-service | 8082 | Go 1.22 + Gin | 재고 관리 + 실시간 차감 | 99.95% |
| notification-service | 8083 | Python 3.12 + FastAPI | 알림 발송 (이메일/SMS/푸시) | 99.9% |
| user-service | 8084 | Java 21 + Spring Boot 3.2 | 회원 관리 + 인증 | 99.99% |
| search-service | 8085 | Python 3.12 + FastAPI | 상품 검색 (Elasticsearch) | 99.9% |

### 2.2 인프라 서비스

| 서비스 | 역할 | 기술 |
|--------|------|------|
| api-gateway | 라우팅 + 인증 + 레이트리밋 | Kong 3.5 |
| config-server | 중앙 설정 관리 | Spring Cloud Config |
| service-registry | 서비스 디스커버리 | Consul |
| message-broker | 비동기 메시지 처리 | RabbitMQ 3.13 |

## 3. 데이터 흐름

### 3.1 주문 생성 흐름

```
클라이언트 → api-gateway → order-api
  ① 주문 생성 (PostgreSQL에 저장, 상태: PENDING)
  ② 재고 확인 요청 → inventory-service (gRPC)
     └─ 재고 부족 시 → 주문 상태 REJECTED, 클라이언트에 즉시 응답
  ③ 재고 차감 (Redis Lock으로 동시성 제어)
  ④ 결제 요청 발행 → RabbitMQ (order.payment.requested)
  ⑤ 클라이언트에 ACCEPTED 응답

payment-service (RabbitMQ 소비)
  ⑥ PG사 결제 API 호출
  ⑦ 결제 성공 → 이벤트 발행 (payment.completed)
  ⑧ 결제 실패 → 이벤트 발행 (payment.failed)
     └─ 보상 트랜잭션: 재고 복원 요청 → inventory-service

order-api (이벤트 소비)
  ⑨ payment.completed → 주문 상태 CONFIRMED
  ⑩ payment.failed → 주문 상태 CANCELLED, 재고 복원 확인

notification-service (이벤트 소비)
  ⑪ 주문 확정/취소 시 고객에게 알림 발송
```

### 3.2 주문 취소 흐름

- 결제 전 취소: 즉시 처리 (재고 복원)
- 결제 후 취소: PG 환불 API 호출 → 환불 완료 후 재고 복원
- 배송 시작 후: 취소 불가 (반품 절차 안내)

### 3.3 데이터 정합성

- **Saga 패턴**: 주문-결제-재고 간 분산 트랜잭션 관리
- **Outbox 패턴**: 이벤트 유실 방지 (DB에 먼저 기록 → 별도 발행)
- **멱등성 키**: 결제 요청 시 orderId를 멱등성 키로 사용 (중복 결제 방지)

## 4. 데이터베이스

### 4.1 서비스별 DB (Database per Service)

| 서비스 | DB | 스키마 |
|--------|------|--------|
| order-api | PostgreSQL 16 | orders, order_items, order_history |
| payment-service | PostgreSQL 16 | payments, refunds |
| inventory-service | PostgreSQL 16 + Redis 7 | products, stock (Redis: 실시간 재고) |
| user-service | PostgreSQL 16 | users, roles, sessions |
| search-service | Elasticsearch 8.12 | products_index |
| notification-service | MongoDB 7 | notifications, templates |

### 4.2 캐시 전략

- **user-service**: 세션 캐시 (Redis, TTL 30분)
- **inventory-service**: 재고 캐시 (Redis, Write-Through)
- **search-service**: 검색 결과 캐시 (Redis, TTL 5분)
- **order-api**: 주문 상세 캐시 없음 (항상 최신 데이터 보장)

## 5. 인프라 및 배포

### 5.1 인프라 구성

- **클라우드**: AWS (서울 리전)
- **오케스트레이션**: EKS (Kubernetes 1.29)
- **네트워크**: VPC + Private Subnet, NAT Gateway
- **로드밸런서**: ALB (L7) → Ingress Controller → Service

### 5.2 CI/CD 파이프라인

```
GitHub → GitHub Actions
  ① 린트 + 단위 테스트
  ② 도커 이미지 빌드 → ECR 푸시
  ③ 스테이징 배포 (자동)
  ④ 통합 테스트 (자동)
  ⑤ 프로덕션 배포 (수동 승인)
```

- 롤링 배포 기본, 주요 변경 시 Blue/Green
- 카나리 배포: 트래픽 5% → 20% → 50% → 100% (최소 30분 간격)

### 5.3 모니터링

| 영역 | 도구 | 알림 |
|------|------|------|
| 메트릭 | Prometheus + Grafana | PagerDuty (P1/P2) |
| 로그 | Loki + Grafana | Slack (#ops-alerts) |
| 트레이싱 | Jaeger | - |
| APM | 없음 (Jaeger로 대체) | - |
| 가동률 | Uptime Robot | PagerDuty (P1) |

### 5.4 성능 기준

| 지표 | 목표 | 현재 |
|------|------|------|
| API 응답시간 p95 | < 200ms | 180ms |
| 주문 처리 TPS | 1,200 | 1,150 |
| 가동률 | 99.95% | 99.97% |
| 에러율 | < 0.1% | 0.05% |
| 배포 주기 | 주 2회 | 주 3회 |

## 6. 보안

### 6.1 인증/인가

- **인증**: JWT (Access Token 15분 + Refresh Token 7일)
- **인가**: RBAC (Admin, Manager, Operator, Viewer)
- **API Gateway**: JWT 검증 + Rate Limiting (사용자당 100 req/min)

### 6.2 데이터 보호

- 전송: TLS 1.3 (서비스 간 mTLS)
- 저장: AES-256 (PII 컬럼 암호화)
- 결제 정보: PCI DSS 준수 (PG사 토큰화, 카드번호 미저장)

### 6.3 접근 제어

- DB 직접 접근: DBA만 허용 (Bastion 경유, 2FA)
- 프로덕션 SSH: 금지 (kubectl exec도 감사 로그)
- 시크릿 관리: AWS Secrets Manager + External Secrets Operator
