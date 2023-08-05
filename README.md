![Banner](https://github.com/wakscord/node-v2/assets/36909737/a01b11de-48a0-41ed-82d1-dc62f9f4b6e2)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/wakscord/node-v2/main.svg)](https://results.pre-commit.ci/latest/github/wakscord/node-v2/main)


# 왁스코드 노드

왁스코드 구독자 분들에게 왁타버스 멤버들의 채팅을 전송하는 서버입니다.

## 설정

### Python 가상환경 설정

가상환경 생성 후 패키지를 설치합니다.
```shell
python -m venv venv # 가상환경 생성

source venv/bin/activate # 가상환경 활성화

python -m pip install -r requirements.txt # 패키지 설치
```

### Pre-commit 설정

pre-commit은 formatting, linting, type checking을 커밋 이전에 수행합니다.

아래 목록의 라이브러리를 사용하고 있습니다.

- import formatting: isort
- formatting: black
- convention: pep8 (flake8)
- type checking: mypy

<br/>

pre-commit hooks를 install 합니다.

```shell
pre-commit install
```

## 실행

### .env 설정

sample 파일을 복사해서 .env 파일을 생성합니다.

```shell
cp .env.sample .env
```

.env는 다음 목록으로 구성돼 있습니다.

```dotenv
MAX_CONCURRENT=2000         # 동시 메시지 전송 수 (optional)
REDIS_URL=localhost         # 레디스 URL (required)
REDIS_PORT=6379             # 레디스 포트  (optional)
REDIS_PASSWORD={password}   # 레디스 비밀번호 (optional)
PROXY_USER={user}           # 프록시 아이디 (optional)
PROXY_PASSWORD={password}   # 프록시 비밀번호 (optional)
```

.env 설정 후에 아래 스크립트를 통해서 서버를 실행합니다.

```shell
./dev.sh
```

# test
