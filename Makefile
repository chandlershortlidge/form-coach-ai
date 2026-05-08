PROJECT_ID=sodium-daylight-457415-r0
REGION=europe-west1
BACKEND_URL=https://fitness-form-coach-t32qh37koa-ew.a.run.app
FRONTEND_URL=https://fitness-form-coach-frontend-959217952961.europe-west1.run.app
 
BACKEND_IMAGE=gcr.io/$(PROJECT_ID)/fitness-form-coach:latest
FRONTEND_IMAGE=gcr.io/$(PROJECT_ID)/fitness-form-coach-frontend:latest
 
# Deploy both services
deploy: deploy-backend deploy-frontend
 
# Backend
build-backend:
	docker build --platform linux/amd64 -t $(BACKEND_IMAGE) .
 
push-backend:
	docker push $(BACKEND_IMAGE)
 
deploy-backend: build-backend push-backend
	gcloud run services update fitness-form-coach \
		--region $(REGION) \
		--image $(BACKEND_IMAGE) \
		--set-env-vars CORS_ALLOWED_ORIGINS=$(FRONTEND_URL)
 
# Frontend
build-frontend:
	docker build --platform linux/amd64 \
		--build-arg VITE_API_URL=$(BACKEND_URL) \
		-t $(FRONTEND_IMAGE) \
		frontend/
 
push-frontend:
	docker push $(FRONTEND_IMAGE)
 
deploy-frontend: build-frontend push-frontend
	gcloud run services update fitness-form-coach-frontend \
		--region $(REGION) \
		--image $(FRONTEND_IMAGE)