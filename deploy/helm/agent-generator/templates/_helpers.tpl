{{/*
Chart helpers.
*/}}
{{- define "agent-generator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "agent-generator.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "agent-generator.backendFullname" -}}
{{ include "agent-generator.fullname" . }}-backend
{{- end -}}

{{- define "agent-generator.webFullname" -}}
{{ include "agent-generator.fullname" . }}-web
{{- end -}}

{{- define "agent-generator.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "agent-generator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "agent-generator.backendImage" -}}
{{ printf "%s/%s:%s" .Values.global.registry .Values.backend.image.repository .Values.backend.image.tag }}
{{- end -}}

{{- define "agent-generator.webImage" -}}
{{ printf "%s/%s:%s" .Values.global.registry .Values.web.image.repository .Values.web.image.tag }}
{{- end -}}
