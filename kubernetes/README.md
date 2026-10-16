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

Адрес снаружи. Docker Desktop обычно даёт `localhost`. Иначе возьмите IP ноды:

```bash
kubectl get svc frontend
```

```bash
curl http://127.0.0.1:30080/
curl http://127.0.0.1:30080/health
```

На Windows PowerShell: `curl.exe`.

Повторите `GET /` несколько раз. В JSON поле `replica` — имя пода backend. При трёх репликах имена чередуются. Заголовок `X-Forwarded-By: frontend` показывает, что ответ пришёл через точку входа.

Прямой доступ к backend снаружи закрыт:

```bash
kubectl get svc backend
```

У него только ClusterIP. Запрос из кластера:

```bash
kubectl exec deploy/frontend -- python -c "import urllib.request; print(urllib.request.urlopen('http://backend:8080/').read().decode())"
```

## Остановка

```bash
kubectl delete -f frontend-service.yaml -f frontend-deployment.yaml -f backend-service.yaml -f backend-deployment.yaml
kind delete cluster --name cloud-k8s
```
