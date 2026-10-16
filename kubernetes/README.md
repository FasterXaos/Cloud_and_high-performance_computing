# Frontend и backend в Kubernetes

Frontend слушает снаружи и пересылает HTTP на backend. Backend отвечает изнутри кластера и запущен в трёх репликах. Снаружи backend не опубликован: к нему можно обратиться только через Service `backend` с ClusterIP.

Образы собираются локально, в манифестах стоит `imagePullPolicy: IfNotPresent`.

## Что чем является

| Файл | Роль |
| --- | --- |
| `backend-deployment.yaml` | Три пода backend |
| `backend-service.yaml` | ClusterIP `backend:8080` внутри кластера |
| `frontend-deployment.yaml` | Один под frontend, ходит на `http://backend:8080` |
| `frontend-service.yaml` | LoadBalancer на порт 80, запасной NodePort `30080` |
| `backend/` | Образ API |
| `frontend/` | Образ точки входа |

Нужны Docker, `kubectl` и включённый Kubernetes (Docker Desktop, minikube или kind). Локально проверено через kind: конфиг `kind-config.yaml` пробрасывает NodePort `30080` на хост.

## Сборка образов

Из этой папки:

```bash
docker build -t cloud-k8s-backend:1.0 ./backend
docker build -t cloud-k8s-frontend:1.0 ./frontend
```

Если кластер — kind:

```bash
kind create cluster --config kind-config.yaml
kind load docker-image cloud-k8s-backend:1.0 --name cloud-k8s
kind load docker-image cloud-k8s-frontend:1.0 --name cloud-k8s
```

Для minikube собирайте в его Docker:

```bash
minikube docker-env | Invoke-Expression
```

## Запуск

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
kubectl get pods,svc -w
```

Дождитесь, пока поды станут Ready. У frontend Service появится `EXTERNAL-IP` или останется `<pending>` — тогда используйте NodePort.

## Проверка

Все команды ниже вводятся в том же терминале, из папки `kubernetes`, после того как `kubectl get pods` показывает четыре Ready. На Windows вместо `curl` пишите `curl.exe`.

**1. Посмотреть сервисы.** Нужно увидеть `frontend` типа LoadBalancer и `backend` типа ClusterIP.

```bash
kubectl get svc
```

У `frontend` колонка `PORT(S)` выглядит как `80:30080/TCP`. Это внешний порт `30080` на машине. `EXTERNAL-IP` у kind часто `<pending>` — тогда ходите на `http://127.0.0.1:30080`. Если там уже есть адрес (Docker Desktop часто даёт `localhost`), можно открывать `http://<этот-адрес>/`.

**2. Проверить, что точка входа жива.** Это ответ самого frontend, без backend.

```bash
curl.exe -sS http://127.0.0.1:30080/health
```

Ожидается: `{"service":"frontend","status":"ok"}`.

**3. Запросить данные через frontend.** Запрос идёт с хоста на frontend, frontend пересылает его backend.

```bash
curl.exe -sS -D - http://127.0.0.1:30080/
```

Ожидается заголовок `X-Forwarded-By: frontend` и JSON вида `{"message":"request received","replica":"backend-...","service":"backend"}`. Поле `replica` — имя пода, который ответил.

**4. Повторить шаг 3 ещё четыре-пять раз.** Имена в `replica` должны меняться между тремя подами backend. Так видно, что запросы распределяются по репликам.

**5. Убедиться, что backend снаружи не опубликован.**

```bash
kubectl get svc backend
```

Тип только `ClusterIP`, внешнего порта нет. С хоста `http://127.0.0.1:8080` к этому backend не относится.

**6. Сходить в backend изнутри кластера.** Команда выполняется в поде frontend и бьёт во внутреннее имя сервиса `backend`.

```bash
kubectl exec deploy/frontend -- python -c "import urllib.request; print(urllib.request.urlopen('http://backend:8080/').read().decode())"
```

Ожидается тот же JSON backend с полем `replica`. Это и есть путь, которым frontend ходит в обычном режиме.

## Остановка

```bash
kubectl delete -f frontend-service.yaml -f frontend-deployment.yaml -f backend-service.yaml -f backend-deployment.yaml
kind delete cluster --name cloud-k8s
```
