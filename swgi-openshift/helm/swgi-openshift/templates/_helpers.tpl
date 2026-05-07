{{- define "swgi-openshift.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "swgi-openshift.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "swgi-openshift.name" . -}}
{{- end -}}
{{- end -}}

{{- define "swgi-openshift.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "swgi-openshift.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
