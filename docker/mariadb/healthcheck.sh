#!/bin/bash
# MariaDB health check script for Comuniza production
# Used by Docker healthcheck

mysqladmin ping -h localhost -u root -ppassword123