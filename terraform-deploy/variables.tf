variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "drangue"
}

variable "region" {
  description = "The region the environment is going to be installed into"
  type        = string
  default     = "ap-southeast-1"
}

# VPC variables
variable "vpc_id" {
  description = "ID of the VPC"
  default     = "vpc-9a40a1fd"
}

variable "vpc_cidr" {
  description = "CIDR range of VPC"
  type        = string
  default     = "10.0.0.0/16"
}


# Project specific variables
variable "firebase_api_key" {
  description = "Value of the firebase api key"
  type        = string
}

variable "firebase_auth_domain" {
  description = "Value of the firebase auth domain"
  type        = string
}


variable "firebase_database_url" {
  description = "Value of the firebase db url"
  type        = string
}


variable "firebase_project_id" {
  description = "Value of the firebase project id"
  type        = string
}

variable "firebase_storage_bucket" {
  description = "Value of the firebase storage bucket"
  type        = string 
}

variable "firebase_messaging_sender_id" {
  description = "Value of the firebase messaging sender id"
  type        = string  
}

variable "firebase_app_id" {
  description = "Value of the firebase app id"
  type        = string
}

variable "mailer_sender_api_key" {
  description = "Value of the mailer sender api key"
  type        = string
}

variable "gdal_data" {
  description = "Value of the GDAL data"
  type        = string
}

variable "proj_lib" {
  description = "Value of the PROJ lib"
  type        = string
}

