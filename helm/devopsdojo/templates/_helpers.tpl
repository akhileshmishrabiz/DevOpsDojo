{{/*
Expand the name of the chart.
*/}}
{{- define "devopsdojo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devopsdojo.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "devopsdojo.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devopsdojo.labels" -}}
helm.sh/chart: {{ include "devopsdojo.chart" . }}
{{ include "devopsdojo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devopsdojo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devopsdojo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "devopsdojo.backend.labels" -}}
{{ include "devopsdojo.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "devopsdojo.backend.selectorLabels" -}}
{{ include "devopsdojo.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "devopsdojo.frontend.labels" -}}
{{ include "devopsdojo.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "devopsdojo.frontend.selectorLabels" -}}
{{ include "devopsdojo.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "devopsdojo.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devopsdojo.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Backend service name
*/}}
{{- define "devopsdojo.backend.serviceName" -}}
{{- printf "%s-backend" (include "devopsdojo.fullname" .) }}
{{- end }}

{{/*
Frontend service name
*/}}
{{- define "devopsdojo.frontend.serviceName" -}}
{{- printf "%s-frontend" (include "devopsdojo.fullname" .) }}
{{- end }}

{{/*
Database service name
*/}}
{{- define "devopsdojo.database.serviceName" -}}
{{- printf "%s-postgres" (include "devopsdojo.fullname" .) }}
{{- end }}

{{/*
Database host
*/}}
{{- define "devopsdojo.database.host" -}}
{{- if .Values.database.external.enabled }}
{{- .Values.database.external.host }}
{{- else }}
{{- include "devopsdojo.database.serviceName" . }}.{{ .Release.Namespace }}.svc.cluster.local
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "devopsdojo.database.url" -}}
{{- $host := include "devopsdojo.database.host" . }}
{{- $port := .Values.database.external.port | default "5432" }}
{{- $name := .Values.database.external.name | default "postgres" }}
{{- printf "postgresql://$(DB_USERNAME):$(DB_PASSWORD)@%s:%s/%s" $host $port $name }}
{{- end }}

{{/*
Backend URL for frontend
*/}}
{{- define "devopsdojo.backend.url" -}}
{{- if .Values.frontend.env.backendUrl }}
{{- .Values.frontend.env.backendUrl }}
{{- else }}
{{- printf "http://%s.%s.svc.cluster.local:%d" (include "devopsdojo.backend.serviceName" .) .Release.Namespace (int .Values.backend.service.port) }}
{{- end }}
{{- end }}

{{/*
ConfigMap name
*/}}
{{- define "devopsdojo.configMapName" -}}
{{- printf "%s-config" (include "devopsdojo.fullname" .) }}
{{- end }}

{{/*
Secret name
*/}}
{{- define "devopsdojo.secretName" -}}
{{- printf "%s-secrets" (include "devopsdojo.fullname" .) }}
{{- end }}

{{/*
Namespace
*/}}
{{- define "devopsdojo.namespace" -}}
{{- .Values.global.namespace | default .Release.Namespace }}
{{- end }}
