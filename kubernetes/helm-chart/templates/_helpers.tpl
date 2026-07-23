{{- define "shelfsense.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "shelfsense.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" -}}
{{- end -}}

{{- define "shelfsense.labels" -}}
helm.sh/chart: {{ include "shelfsense.chart" . }}
app.kubernetes.io/name: {{ include "shelfsense.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/part-of: shelfsense-it
{{- end -}}

{{- define "shelfsense.postgres.selectorLabels" -}}
app.kubernetes.io/name: {{ include "shelfsense.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: postgres
{{- end -}}

{{- define "shelfsense.postgres.configMapName" -}}
{{- printf "%s-postgres-config" .Release.Name -}}
{{- end -}}

{{- define "shelfsense.postgres.secretName" -}}
{{- printf "%s-postgres-secret" .Release.Name -}}
{{- end -}}
