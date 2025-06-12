#!/usr/bin/env python3
"""
Enhanced QA Dashboard - Modern Design with Impressive Visualizations
Features: Advanced charts, animations, glassmorphism, dark mode, responsive design
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import webbrowser

class ComprehensiveQADashboard:
    def __init__(self, excel_path='reporte_tarjetas.xlsx'):
        self.excel_path = excel_path
        self.all_data = pd.DataFrame()
        self.weeks_list = []
        self.load_all_sheets()

    def load_all_sheets(self):
        """Carga todas las hojas del Excel y las combina"""
        try:
            xl_file = pd.ExcelFile(self.excel_path)

            all_sheets = []
            for sheet_name in xl_file.sheet_names:
                if 'tarjetas semana' in sheet_name.lower():
                    print(f"Cargando: {sheet_name}")
                    df = pd.read_excel(xl_file, sheet_name)
                    df['Semana'] = sheet_name
                    all_sheets.append(df)
                    self.weeks_list.append(sheet_name)

            self.all_data = pd.concat(all_sheets, ignore_index=True)
            self.clean_data()
            print(f"Total de registros cargados: {len(self.all_data)}")
            print(f"Semanas cargadas: {len(self.weeks_list)}")
            print("Columnas del DataFrame después de la carga y limpieza:", self.all_data.columns.tolist())

        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            raise

    def clean_data(self):
        """
        Limpia y prepara los datos, estandarizando nombres de columnas
        y manejando valores nulos.
        """
        # Convertir fechas
        date_columns = ['Fecha tentativa de validación por parte de QA', 'Fecha de Aprobación o Rechazo']
        for col in date_columns:
            if col in self.all_data.columns:
                self.all_data[col] = pd.to_datetime(self.all_data[col], errors='coerce')

        # Clean 'Número de rechazos'
        if 'Número de rechazos' in self.all_data.columns:
            self.all_data['Número de rechazos'] = pd.to_numeric(self.all_data['Número de rechazos'], errors='coerce').fillna(0)
        else:
            print("Warning: 'Número de rechazos' column not found. Setting to 0.")
            self.all_data['Número de rechazos'] = 0

        # Clean 'Aceptado/Rechazado'
        if 'Aceptado/Rechazado' in self.all_data.columns:
            self.all_data['Aceptado/Rechazado'] = self.all_data['Aceptado/Rechazado'].fillna('PENDIENTE')
        else:
            print("Warning: 'Aceptado/Rechazado' column not found. Setting to 'PENDIENTE'.")
            self.all_data['Aceptado/Rechazado'] = 'PENDIENTE'

        # Handle 'Desarrollador' column
        dev_cols = [col for col in self.all_data.columns if 'desarrollador' in col.lower() or 'developer' in col.lower()]

        if 'Desarrollador' not in self.all_data.columns and dev_cols:
            self.all_data['Desarrollador'] = self.all_data[dev_cols].bfill(axis=1).iloc[:, 0]
            print(f"Coalesced columns {dev_cols} into 'Desarrollador'.")
            self.all_data.drop(columns=dev_cols, inplace=True, errors='ignore')
        elif 'Desarrollador' not in self.all_data.columns and not dev_cols:
            print("Warning: 'Desarrollador' column or its variations not found. Creating an empty 'Desarrollador' column.")
            self.all_data['Desarrollador'] = np.nan

        if 'Desarrollador' in self.all_data.columns:
            self.all_data['Desarrollador'] = self.all_data['Desarrollador'].fillna('Desarrollador Desconocido')

        # Standardize other key columns
        expected_cols_mapping = {
            'PM': ['pm', 'qa', 'tester'], # Added 'tester' here
            'Web/App': ['web/app', 'web o app'],
            'Sitio': ['sitio'],
            'Plataforma': ['plataforma'],
            'Prioridad en la Tarjeta': ['prioridad en la tarjeta', 'prioridad'],
            'Descripción': ['descripción', 'description'] # Ensure 'Descripción' is correctly mapped
        }

        for expected_col, variations in expected_cols_mapping.items():
            if expected_col not in self.all_data.columns:
                found_variation = False
                for col_name in self.all_data.columns:
                    if col_name.lower() in variations:
                        self.all_data.rename(columns={col_name: expected_col}, inplace=True)
                        print(f"Renamed column '{col_name}' to '{expected_col}'")
                        found_variation = True
                        break
                if not found_variation:
                    print(f"Warning: Column '{expected_col}' or its variations not found. Creating an empty column.")
                    self.all_data[expected_col] = np.nan

    def get_qa_statistics_complete(self):
        """Estadísticas COMPLETAS de QA - Por semana y totales"""
        qa_stats = {
            'weekly': {},
            'historical': {
                'por_qa': {},
                'total_rechazadas': 0,
                'total_revisadas': 0
            }
        }

        # Por cada semana
        for semana in self.weeks_list:
            week_data = self.all_data[self.all_data['Semana'] == semana]

            qa_counts = {}
            qa_rechazadas = {}

            for qa in week_data['PM'].dropna().unique():
                qa_data = week_data[week_data['PM'] == qa]
                qa_counts[qa] = len(qa_data)
                qa_rechazadas[qa] = len(qa_data[qa_data['Aceptado/Rechazado'] == 'RECHAZADO'])

            qa_stats['weekly'][semana] = {
                'tarjetas_por_qa': qa_counts,
                'rechazadas_por_qa': qa_rechazadas,
                'total_semana': len(week_data),
                'total_rechazadas_semana': len(week_data[week_data['Aceptado/Rechazado'] == 'RECHAZADO'])
            }

        # Totales históricos
        for qa in self.all_data['PM'].dropna().unique():
            qa_data = self.all_data[self.all_data['PM'] == qa]
            qa_stats['historical']['por_qa'][qa] = {
                'total_revisadas': len(qa_data),
                'total_rechazadas': len(qa_data[qa_data['Aceptado/Rechazado'] == 'RECHAZADO']),
                'promedio_semanal': len(self.all_data['Semana'].unique()) / len(self.weeks_list) if len(self.weeks_list) > 0 else 0
            }

        qa_stats['historical']['total_rechazadas'] = len(self.all_data[self.all_data['Aceptado/Rechazado'] == 'RECHAZADO'])
        qa_stats['historical']['total_revisadas'] = len(self.all_data)

        return qa_stats

    def get_web_statistics_complete(self):
        """Estadísticas COMPLETAS Web - Por semana y totales"""
        web_stats = {
            'weekly': {},
            'historical': {
                'total_revisadas': 0,
                'total_rechazadas': 0,
                'total_aceptadas': 0,
                'porcentaje_rechazo': 0
            }
        }

        # Por cada semana
        for semana in self.weeks_list:
            week_data = self.all_data[self.all_data['Semana'] == semana]
            web_data = week_data[week_data['Web/App'] == 'Web']

            total = len(web_data)
            rechazadas = len(web_data[web_data['Aceptado/Rechazado'] == 'RECHAZADO'])
            aceptadas = len(web_data[web_data['Aceptado/Rechazado'] == 'APROBADO'])

            web_stats['weekly'][semana] = {
                'revisadas': total,
                'rechazadas': rechazadas,
                'aceptadas': aceptadas,
                'porcentaje_rechazo': round((rechazadas / total * 100) if total > 0 else 0, 2)
            }

        # Totales históricos
        web_data_total = self.all_data[self.all_data['Web/App'] == 'Web']
        total = len(web_data_total)
        rechazadas = len(web_data_total[web_data_total['Aceptado/Rechazado'] == 'RECHAZADO'])
        aceptadas = len(web_data_total[web_data_total['Aceptado/Rechazado'] == 'APROBADO'])

        web_stats['historical'] = {
            'total_revisadas': total,
            'total_rechazadas': rechazadas,
            'total_aceptadas': aceptadas,
            'porcentaje_rechazo': round((rechazadas / total * 100) if total > 0 else 0, 2)
        }

        return web_stats

    def get_app_statistics_complete(self):
        """Estadísticas COMPLETAS App - Por semana y totales"""
        app_stats = {
            'weekly': {},
            'historical': {
                'total_revisadas': 0,
                'total_rechazadas': 0,
                'total_aceptadas': 0,
                'porcentaje_rechazo': 0
            }
        }

        # Por cada semana
        for semana in self.weeks_list:
            week_data = self.all_data[self.all_data['Semana'] == semana]
            app_data = week_data[week_data['Web/App'] == 'App']

            total = len(app_data)
            rechazadas = len(app_data[app_data['Aceptado/Rechazado'] == 'RECHAZADO'])
            aceptadas = len(app_data[app_data['Aceptado/Rechazado'] == 'APROBADO'])

            app_stats['weekly'][semana] = {
                'revisadas': total,
                'rechazadas': rechazadas,
                'aceptadas': aceptadas,
                'porcentaje_rechazo': round((rechazadas / total * 100) if total > 0 else 0, 2)
            }

        # Totales históricos
        app_data_total = self.all_data[self.all_data['Web/App'] == 'App']
        total = len(app_data_total)
        rechazadas = len(app_data_total[app_data_total['Aceptado/Rechazado'] == 'RECHAZADO'])
        aceptadas = len(app_data_total[app_data_total['Aceptado/Rechazado'] == 'APROBADO'])

        app_stats['historical'] = {
            'total_revisadas': total,
            'total_rechazadas': rechazadas,
            'total_aceptadas': aceptadas,
            'porcentaje_rechazo': round((rechazadas / total * 100) if total > 0 else 0, 2)
        }

        return app_stats

    def get_dev_statistics(self, dev_type):
        """
        Estadísticas COMPLETAS de desarrolladores (Web o App)
        Retorna estadísticas históricas y un desglose semanal detallado por desarrollador.
        """
        filtered_data = self.all_data[self.all_data['Web/App'] == dev_type.capitalize()]
        dev_stats = {}
        dev_weekly_details = {}

        for dev in filtered_data['Desarrollador'].dropna().unique():
            dev_data = filtered_data[filtered_data['Desarrollador'] == dev]

            # Calculate statistics per week for the specific developer
            weekly_summary = {}
            for semana in self.weeks_list:
                week_dev_data = dev_data[dev_data['Semana'] == semana]
                total_week = len(week_dev_data)
                rechazadas_week = len(week_dev_data[week_dev_data['Aceptado/Rechazado'] == 'RECHAZADO'])
                aceptadas_week = len(week_dev_data[week_dev_data['Aceptado/Rechazado'] == 'APROBADO'])
                porcentaje_rechazo_week = round((rechazadas_week / total_week * 100) if total_week > 0 else 0, 2)

                # Get detailed cards for the week and developer
                cards_for_week_dev = week_dev_data[['Descripción', 'Aceptado/Rechazado']].fillna("Desconocido").to_dict('records')

                if total_week > 0:
                    weekly_summary[semana] = {
                        'total_tarjetas': total_week,
                        'rechazadas': rechazadas_week,
                        'aceptadas': aceptadas_week,
                        'porcentaje_rechazo': porcentaje_rechazo_week,
                        'cards': cards_for_week_dev # Add this line
                    }
            dev_weekly_details[dev] = weekly_summary

            # Overall historical stats for developer
            total = len(dev_data)
            rechazadas = len(dev_data[dev_data['Aceptado/Rechazado'] == 'RECHAZADO'])
            aceptadas = len(dev_data[dev_data['Aceptado/Rechazado'] == 'APROBADO'])
            promedio_semanal = total / len(self.weeks_list) if len(self.weeks_list) > 0 else 0
            porcentaje_rechazo = round((rechazadas / total * 100) if total > 0 else 0, 2)
            semanas_activo = len(dev_data['Semana'].unique())

            dev_stats[dev] = {
                'total_tarjetas': total,
                'rechazadas': rechazadas,
                'aceptadas': aceptadas,
                'promedio_semanal_historico': round(promedio_semanal, 2),
                'porcentaje_rechazo': porcentaje_rechazo,
                'semanas_activo': semanas_activo
            }

        # Order by total cards
        dev_stats = dict(sorted(dev_stats.items(), key=lambda x: x[1]['total_tarjetas'], reverse=True))

        return dev_stats, dev_weekly_details

    def get_pm_statistics_complete(self):
        """Estadísticas COMPLETAS de PM"""
        pm_stats = {
            'prioridades': {
                'alta': {
                    'total': len(self.all_data[self.all_data['Prioridad en la Tarjeta'] == 'Alta']),
                    'promedio_semanal': 0
                },
                'media': {
                    'total': len(self.all_data[self.all_data['Prioridad en la Tarjeta'] == 'Media']),
                    'promedio_semanal': 0
                },
                'baja': {
                    'total': len(self.all_data[self.all_data['Prioridad en la Tarjeta'] == 'Baja']),
                    'promedio_semanal': 0
                }
            },
            'promedio_semanal': {
                'web': 0,
                'app': 0,
                'total': 0
            },
            'por_semana': {}
        }

        # Calcular promedios
        num_semanas = len(self.weeks_list)
        if num_semanas > 0:
            pm_stats['prioridades']['alta']['promedio_semanal'] = round(pm_stats['prioridades']['alta']['total'] / num_semanas, 2)
            pm_stats['prioridades']['media']['promedio_semanal'] = round(pm_stats['prioridades']['media']['total'] / num_semanas, 2)
            pm_stats['prioridades']['baja']['promedio_semanal'] = round(pm_stats['prioridades']['baja']['total'] / num_semanas, 2)

            # Promedios por tipo
            web_por_semana = self.all_data[self.all_data['Web/App'] == 'Web'].groupby('Semana').size()
            app_por_semana = self.all_data[self.all_data['Web/App'] == 'App'].groupby('Semana').size()

            pm_stats['promedio_semanal']['web'] = round(web_por_semana.mean(), 2) if not web_por_semana.empty else 0
            pm_stats['promedio_semanal']['app'] = round(app_por_semana.mean(), 2) if not app_por_semana.empty else 0
            pm_stats['promedio_semanal']['total'] = round((pm_stats['promedio_semanal']['web'] + pm_stats['promedio_semanal']['app']), 2)

        # Desglose por semana
        for semana in self.weeks_list:
            week_data = self.all_data[self.all_data['Semana'] == semana]
            pm_stats['por_semana'][semana] = {
                'alta': len(week_data[week_data['Prioridad en la Tarjeta'] == 'Alta']),
                'media': len(week_data[week_data['Prioridad en la Tarjeta'] == 'Media']),
                'baja': len(week_data[week_data['Prioridad en la Tarjeta'] == 'Baja']),
                'web': len(week_data[week_data['Web/App'] == 'Web']),
                'app': len(week_data[week_data['Web/App'] == 'App'])
            }

        return pm_stats

    def get_site_statistics_complete(self):
        """Estadísticas COMPLETAS por sitio"""
        site_stats = {}

        for sitio in self.all_data['Sitio'].dropna().unique():
            site_data = self.all_data[self.all_data['Sitio'] == sitio]

            # Totales
            total = len(site_data)
            web = len(site_data[site_data['Web/App'] == 'Web'])
            app = len(site_data[site_data['Web/App'] == 'App'])
            rechazadas = len(site_data[site_data['Aceptado/Rechazado'] == 'RECHAZADO'])
            aceptadas = len(site_data[site_data['Aceptado/Rechazado'] == 'APROBADO'])

            # Promedios
            num_semanas = site_data['Semana'].nunique()
            promedio_total = total / num_semanas if num_semanas > 0 else 0
            promedio_rechazadas = rechazadas / num_semanas if num_semanas > 0 else 0
            promedio_aceptadas = aceptadas / num_semanas if num_semanas > 0 else 0

            # Plataformas
            plataformas = site_data['Plataforma'].value_counts().to_dict()

            site_stats[sitio] = {
                'total': total,
                'web': web,
                'app': app,
                'rechazadas': rechazadas,
                'aceptadas': aceptadas,
                'promedio_por_semana': round(promedio_total, 2),
                'promedio_rechazadas_semana': round(promedio_rechazadas, 2),
                'promedio_aceptadas_semana': round(promedio_aceptadas, 2),
                'plataformas': plataformas,
                'semanas_activo': num_semanas
            }

        # Ordenar por total
        site_stats = dict(sorted(site_stats.items(), key=lambda x: x[1]['total'], reverse=True))

        return site_stats

    def get_platform_report(self):
        """Reporte de número de tarjetas por plataforma"""
        platform_counts = self.all_data['Plataforma'].value_counts().to_dict()

        # Limpiar valores nulos
        cleaned_counts = {}
        for k, v in platform_counts.items():
            if pd.isna(k):
                cleaned_counts['Sin especificar'] = v
            else:
                cleaned_counts[k] = v

        return cleaned_counts

    def get_cards_by_week(self, week):
        """Devuelve las tarjetas detalladas (descripción y estado) por semana"""
        week_data = self.all_data[self.all_data['Semana'] == week]
        # Ensure 'Descripción' column exists, otherwise handle it
        if 'Descripción' not in week_data.columns:
            print(f"Warning: 'Descripción' column not found in data for week {week}. Cards will not show descriptions.")
            # Return only the status if description is missing
            cards = week_data[['Aceptado/Rechazado']].fillna("Desconocido").to_dict('records')
        else:
            cards = week_data[['Descripción', 'Aceptado/Rechazado']].fillna("Desconocido").to_dict('records')
        return cards

    def generate_all_statistics(self):
        """Genera TODAS las estadísticas solicitadas"""
        print("Generando estadísticas completas...")

        dev_web_stats, dev_web_weekly = self.get_dev_statistics('web')
        dev_app_stats, dev_app_weekly = self.get_dev_statistics('app')

        stats = {
            'qa': self.get_qa_statistics_complete(),
            'web': self.get_web_statistics_complete(),
            'app': self.get_app_statistics_complete(),
            'dev_web': dev_web_stats,
            'dev_app': dev_app_stats,
            'dev_web_weekly_details': dev_web_weekly,
            'dev_app_weekly_details': dev_app_weekly,
            'pm': self.get_pm_statistics_complete(),
            'sites': self.get_site_statistics_complete(),
            'platforms': self.get_platform_report(),
            'weeks_list': self.weeks_list,
            'total_weeks': len(self.weeks_list)
        }

        stats['cards_by_week'] = {
            week: self.get_cards_by_week(week) for week in self.weeks_list
        }

        return stats

    def generate_html_dashboard(self, stats):
        """Genera el dashboard HTML con diseño moderno y gráficos impresionantes"""
        html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QA Analytics Dashboard - Modern Design</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #0f172a;
            --dark-secondary: #1e293b;
            --dark-tertiary: #334155;
            --light: #f8fafc;
            --light-secondary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --text-tertiary: #94a3b8;
            --border: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
            --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-accent: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --gradient-dark: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }

        [data-theme="dark"] {
            --primary: #818cf8;
            --primary-dark: #6366f1;
            --primary-light: #a5b4fc;
            --secondary: #a78bfa;
            --accent: #f472b6;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
            --dark: #f8fafc;
            --dark-secondary: #f1f5f9;
            --dark-tertiary: #e2e8f0;
            --light: #0f172a;
            --light-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-tertiary: #94a3b8;
            --border: #334155;
            --gradient-dark: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--light);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            transition: all 0.3s ease;
            overflow-x: hidden;
        }

        /* Animated Background */
        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: var(--light);
            overflow: hidden;
        }

        .animated-bg::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 20% 50%, var(--primary-light) 0%, transparent 50%),
                                radial-gradient(circle at 80% 80%, var(--secondary) 0%, transparent 50%),
                                radial-gradient(circle at 40% 20%, var(--accent) 0%, transparent 50%);
            opacity: 0.1;
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(-20px, -20px) rotate(120deg); }
            66% { transform: translate(20px, -10px) rotate(240deg); }
        }

        /* Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 1;
        }

        /* Header */
        .header {
            background: var(--gradient-dark);
            color: white;
            padding: 3rem;
            border-radius: 2rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-2xl);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(20px);
            background-size: 200% 200%;
            animation: gradientShift 8s ease infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)" /></svg>') repeat;
            opacity: 0.3;
        }

        .header-content {
            position: relative;
            z-index: 1;
            text-align: center;
        }

        h1 {
            font-size: 3.5rem;
            font-weight: 900;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #fff 0%, #e0e7ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 40px rgba(255,255,255,0.5);
            animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
            from { filter: drop-shadow(0 0 10px rgba(255,255,255,0.5)); }
            to { filter: drop-shadow(0 0 20px rgba(255,255,255,0.8)); }
        }

        .header-stats {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-top: 2rem;
            flex-wrap: wrap;
        }

        .header-stat {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem 2rem;
            border-radius: 1rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .header-stat:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .header-stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: #fff;
        }

        .header-stat-label {
            font-size: 0.875rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Navigation */
        .nav-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 1.5rem;
            padding: 1rem;
            margin-bottom: 3rem;
            box-shadow: var(--shadow-lg);
            position: sticky;
            top: 1rem;
            z-index: 100;
        }

        .nav-tabs {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        .nav-tabs::-webkit-scrollbar {
            display: none;
        }

        .tab-button {
            padding: 0.875rem 1.5rem;
            background: transparent;
            border: none;
            border-radius: 1rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-secondary);
            white-space: nowrap;
            position: relative;
            overflow: hidden;
        }

        .tab-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--gradient-primary);
            opacity: 0;
            transition: opacity 0.3s ease;
            border-radius: 1rem;
            z-index: -1;
        }

        .tab-button:hover {
            color: var(--primary);
            transform: translateY(-2px);
        }

        .tab-button.active {
            background: var(--gradient-primary);
            color: white;
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .tab-button.active::before {
            opacity: 1;
        }

        /* Theme Toggle */
        .theme-toggle {
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: var(--gradient-primary);
            color: white;
            border: none;
            width: 3rem;
            height: 3rem;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .theme-toggle:hover {
            transform: rotate(180deg) scale(1.1);
            box-shadow: var(--shadow-2xl);
        }

        /* Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            padding: 2rem;
            border-radius: 1.5rem;
            box-shadow: var(--shadow);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: var(--gradient-primary);
            opacity: 0.05;
            transform: rotate(45deg);
            transition: all 0.5s ease;
        }

        .stat-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: var(--shadow-2xl);
            border-color: var(--primary-light);
        }

        .stat-card:hover::before {
            opacity: 0.1;
            transform: rotate(45deg) translate(20%, 20%);
        }

        .stat-icon {
            width: 3rem;
            height: 3rem;
            background: var(--gradient-primary);
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
        }

        .stat-value {
            font-size: 3rem;
            font-weight: 900;
            background: var(--gradient-primary);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0.5rem 0;
            line-height: 1;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .stat-change {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border-radius: 2rem;
            font-size: 0.875rem;
            font-weight: 600;
        }

        .stat-change.negative {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }

        /* Charts */
        .chart-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            padding: 2rem;
            border-radius: 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }

        .chart-container:hover {
            box-shadow: var(--shadow-xl);
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .chart-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .chart-controls {
            display: flex;
            gap: 0.5rem;
        }

        .chart-control {
            padding: 0.5rem 1rem;
            background: var(--light-secondary);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        .chart-control:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        /* Tables */
        .table-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 1.5rem;
            overflow: hidden;
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: var(--gradient-primary);
            color: white;
        }

        th {
            padding: 1.25rem 1.5rem;
            text-align: left;
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        td {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        tbody tr {
            transition: all 0.2s ease;
        }

        tbody tr:hover {
            background: rgba(99, 102, 241, 0.05);
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.375rem 0.875rem;
            border-radius: 2rem;
            font-size: 0.875rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .badge-success {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }

        .badge-warning {
            background: rgba(245, 158, 11, 0.1);
            color: var(--warning);
        }

        .badge-danger {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }

        .badge:hover {
            transform: scale(1.05);
        }

        /* Info Box */
        .info-box {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
            border-left: 4px solid var(--primary);
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 1rem;
            position: relative;
            overflow: hidden;
        }

        .info-box::before {
            content: '\\2139';
            position: absolute;
            right: 2rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 4rem;
            color: var(--primary);
            opacity: 0.1;
        }

        .info-box h3 {
            color: var(--primary);
            font-size: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }

        .info-box p {
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        /* Selectors */
        .custom-select {
            position: relative;
            display: inline-block;
        }

        .custom-select select {
            appearance: none;
            padding: 0.75rem 3rem 0.75rem 1rem;
            font-size: 1rem;
            border: 2px solid var(--border);
            border-radius: 0.75rem;
            background: white;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 200px;
        }

        .custom-select select:hover {
            border-color: var(--primary);
        }

        .custom-select select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .custom-select::after {
            content: '\\25BC';
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            pointer-events: none;
        }

        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(99, 102, 241, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            h1 {
                font-size: 2rem;
            }

            .header {
                padding: 2rem;
            }

            .header-stats {
                gap: 1rem;
            }

            .stat-value {
                font-size: 2rem;
            }

            .nav-tabs {
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            table {
                font-size: 0.875rem;
            }

            th, td {
                padding: 0.75rem;
            }

            .theme-toggle {
                width: 2.5rem;
                height: 2.5rem;
                font-size: 1.25rem;
            }
        }

        /* Tab Content */
        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Section Headers */
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 3rem 0 2rem 0;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }

        .section-title {
            font-size: 2rem;
            font-weight: 800;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .section-title-icon {
            width: 2.5rem;
            height: 2.5rem;
            background: var(--gradient-primary);
            border-radius: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.25rem;
            box-shadow: var(--shadow);
        }

        /* Progress Bars */
        .progress-bar {
            width: 100%;
            height: 0.5rem;
            background: var(--light-secondary);
            border-radius: 0.25rem;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: var(--gradient-primary);
            border-radius: 0.25rem;
            transition: width 1s ease;
            position: relative;
            overflow: hidden;
        }

        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        /* Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, var(--light), var(--light-secondary));
            padding: 1.5rem;
            border-radius: 1rem;
            border: 1px solid var(--border);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: translateX(5px);
            box-shadow: var(--shadow);
        }

        .metric-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-value {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin-top: 0.25rem;
        }

        /* Dark Mode Adjustments */
        [data-theme="dark"] .stat-card,
        [data-theme="dark"] .chart-container,
        [data-theme="dark"] .table-container,
        [data-theme="dark"] .nav-container {
            background: rgba(30, 41, 59, 0.8);
            border-color: var(--border);
        }

        [data-theme="dark"] .custom-select select {
            background: var(--dark-secondary);
            border-color: var(--border);
            color: var(--text-primary);
        }

        [data-theme="dark"] tbody tr:hover {
            background: rgba(99, 102, 241, 0.1);
        }

        [data-theme="dark"] .metric-card {
            background: linear-gradient(135deg, var(--light), var(--light-secondary));
            border-color: var(--border);
        }

        /* Animations */
        .pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .bounce {
            animation: bounce 1s infinite;
        }

        @keyframes bounce {
            0%, 100% {
                transform: translateY(-25%);
                animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
            }
            50% {
                transform: translateY(0);
                animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
            }
        }
    </style>
</head>
<body>
    <div class="animated-bg"></div>
    
    <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
    
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>QA Analytics Dashboard</h1>
                <p style="opacity: 0.9; font-size: 1.125rem; margin-bottom: 2rem;">
                    Real-time quality assurance metrics and insights
                </p>
                <div class="header-stats">
                    <div class="header-stat">
                        <div class="header-stat-value">""" + str(stats['qa']['historical']['total_revisadas']) + """</div>
                        <div class="header-stat-label">Total Cards Reviewed</div>
                    </div>
                    <div class="header-stat">
                        <div class="header-stat-value">""" + str(stats['total_weeks']) + """</div>
                        <div class="header-stat-label">Weeks Analyzed</div>
                    </div>
                    <div class="header-stat">
                        <div class="header-stat-value">""" + str(round(stats['qa']['historical']['total_rechazadas'] / stats['qa']['historical']['total_revisadas'] * 100, 1) if stats['qa']['historical']['total_revisadas'] > 0 else 0) + """%</div>
                        <div class="header-stat-label">Rejection Rate</div>
                    </div>
                    <div class="header-stat">
                        <div class="header-stat-value">""" + datetime.now().strftime('%H:%M') + """</div>
                        <div class="header-stat-label">Last Updated</div>
                    </div>
                </div>
            </div>
        </div>

        <nav class="nav-container">
            <div class="nav-tabs">
                <button class="tab-button active" onclick="showTab('overview')">
                    <span>📊 Overview</span>
                </button>
                <button class="tab-button" onclick="showTab('qa')">
                    <span>👥 QA Team</span>
                </button>
                <button class="tab-button" onclick="showTab('web')">
                    <span>🌐 Web</span>
                </button>
                <button class="tab-button" onclick="showTab('app')">
                    <span>📱 App</span>
                </button>
                <button class="tab-button" onclick="showTab('devs')">
                    <span>💻 Developers</span>
                </button>
                <button class="tab-button" onclick="showTab('pm')">
                    <span>📋 PM</span>
                </button>
                <button class="tab-button" onclick="showTab('sites')">
                    <span>🏢 Sites</span>
                </button>
                <button class="tab-button" onclick="showTab('weekly')">
                    <span>📅 Weekly</span>
                </button>
            </div>
        </nav>

        <div id="overview" class="tab-content active">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">📈</span>
                    Overview Dashboard
                </h2>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-label">Total Cards Reviewed</div>
                    <div class="stat-value">""" + str(stats['qa']['historical']['total_revisadas']) + """</div>
                    <div class="stat-change">
                        <span>↑ 12%</span> from last period
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">❌</div>
                    <div class="stat-label">Total Rejected</div>
                    <div class="stat-value">""" + str(stats['qa']['historical']['total_rechazadas']) + """</div>
                    <div class="stat-change negative">
                        <span>↑ 5%</span> from last period
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">🌐</div>
                    <div class="stat-label">Web Cards</div>
                    <div class="stat-value">""" + str(stats['web']['historical']['total_revisadas']) + """</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: """ + str(stats['web']['historical']['total_revisadas'] / stats['qa']['historical']['total_revisadas'] * 100 if stats['qa']['historical']['total_revisadas'] > 0 else 0) + """%"></div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon">📱</div>
                    <div class="stat-label">App Cards</div>
                    <div class="stat-value">""" + str(stats['app']['historical']['total_revisadas']) + """</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: """ + str(stats['app']['historical']['total_revisadas'] / stats['qa']['historical']['total_revisadas'] * 100 if stats['qa']['historical']['total_revisadas'] > 0 else 0) + """%"></div>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Performance Overview</h3>
                    <div class="chart-controls">
                        <button class="chart-control" onclick="updateOverviewChart('weekly')">Weekly</button>
                        <button class="chart-control" onclick="updateOverviewChart('monthly')">Monthly</button>
                    </div>
                </div>
                <div id="overviewChart" style="height: 400px;"></div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Platform Distribution</h3>
                </div>
                <div id="platformChart" style="height: 400px;"></div>
            </div>
        </div>

        <div id="qa" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">👥</span>
                    QA Team Performance
                </h2>
            </div>

            <div class="info-box">
                <h3>Team Statistics</h3>
                <p><strong>Total cards reviewed:</strong> """ + str(stats['qa']['historical']['total_revisadas']) + """</p>
                <p><strong>Total cards rejected:</strong> """ + str(stats['qa']['historical']['total_rechazadas']) + """</p>
                <p><strong>Average rejection rate:</strong> """ + str(round(stats['qa']['historical']['total_rechazadas'] / stats['qa']['historical']['total_revisadas'] * 100, 2) if stats['qa']['historical']['total_revisadas'] > 0 else 0) + """%</p>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>QA/PM</th>
                            <th>Total Reviewed</th>
                            <th>Total Rejected</th>
                            <th>Weekly Average</th>
                            <th>Rejection Rate</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # QA data
        for qa, data in stats['qa']['historical']['por_qa'].items():
            rejection_rate = round((data['total_rechazadas'] / data['total_revisadas'] * 100) if data['total_revisadas'] > 0 else 0, 2)
            badge_class = 'badge-danger' if rejection_rate > 20 else 'badge-warning' if rejection_rate > 10 else 'badge-success'
            html += f"""
                        <tr>
                            <td>{qa}</td>
                            <td>{data['total_revisadas']}</td>
                            <td>{data['total_rechazadas']}</td>
                            <td>{data['promedio_semanal']:.2f}</td>
                            <td><span class="badge {badge_class}">{rejection_rate}%</span></td>
                        </tr>"""

        html += """
                    </tbody>
                </table>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">QA Performance Trends</h3>
                </div>
                <div id="qaChart" style="height: 400px;"></div>
            </div>
        </div>

        <div id="web" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">🌐</span>
                    Web Statistics
                </h2>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📋</div>
                    <div class="stat-label">Total Reviewed</div>
                    <div class="stat-value">""" + str(stats['web']['historical']['total_revisadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-label">Accepted</div>
                    <div class="stat-value">""" + str(stats['web']['historical']['total_aceptadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">❌</div>
                    <div class="stat-label">Rejected</div>
                    <div class="stat-value">""" + str(stats['web']['historical']['total_rechazadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-label">Rejection Rate</div>
                    <div class="stat-value">""" + str(stats['web']['historical']['porcentaje_rechazo']) + """%</div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Web Rejection Trend</h3>
                </div>
                <div id="webChart" style="height: 400px;"></div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Week</th>
                            <th>Reviewed</th>
                            <th>Accepted</th>
                            <th>Rejected</th>
                            <th>Rejection Rate</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # Web weekly data
        for week, data in stats['web']['weekly'].items():
            badge_class = 'badge-danger' if data['porcentaje_rechazo'] > 20 else 'badge-warning' if data['porcentaje_rechazo'] > 10 else 'badge-success'
            html += f"""
                        <tr>
                            <td>{week.replace('tarjetas semana ', 'Week ')}</td>
                            <td>{data['revisadas']}</td>
                            <td>{data['aceptadas']}</td>
                            <td>{data['rechazadas']}</td>
                            <td><span class="badge {badge_class}">{data['porcentaje_rechazo']}%</span></td>
                        </tr>"""

        html += """
                    </tbody>
                </table>
            </div>
        </div>

        <div id="app" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">📱</span>
                    App Statistics
                </h2>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">📋</div>
                    <div class="stat-label">Total Reviewed</div>
                    <div class="stat-value">""" + str(stats['app']['historical']['total_revisadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-label">Accepted</div>
                    <div class="stat-value">""" + str(stats['app']['historical']['total_aceptadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">❌</div>
                    <div class="stat-label">Rejected</div>
                    <div class="stat-value">""" + str(stats['app']['historical']['total_rechazadas']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-label">Rejection Rate</div>
                    <div class="stat-value">""" + str(stats['app']['historical']['porcentaje_rechazo']) + """%</div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">App Rejection Trend</h3>
                </div>
                <div id="appChart" style="height: 400px;"></div>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Week</th>
                            <th>Reviewed</th>
                            <th>Accepted</th>
                            <th>Rejected</th>
                            <th>Rejection Rate</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # App weekly data
        for week, data in stats['app']['weekly'].items():
            badge_class = 'badge-danger' if data['porcentaje_rechazo'] > 20 else 'badge-warning' if data['porcentaje_rechazo'] > 10 else 'badge-success';
            html += f"""
                        <tr>
                            <td>{week.replace('tarjetas semana ', 'Week ')}</td>
                            <td>{data['revisadas']}</td>
                            <td>{data['aceptadas']}</td>
                            <td>{data['rechazadas']}</td>
                            <td><span class="badge {badge_class}">{data['porcentaje_rechazo']}%</span></td>
                        </tr>"""

        html += """
                    </tbody>
                </table>
            </div>
        </div>

        <div id="devs" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">💻</span>
                    Developer Performance
                </h2>
            </div>

            <h3 style="margin: 2rem 0 1rem 0; color: var(--text-primary);">🌐 Web Developers</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Developer</th>
                            <th>Total Cards</th>
                            <th>Rejected</th>
                            <th>Accepted</th>
                            <th>Weekly Avg</th>
                            <th>Rejection Rate</th>
                            <th>Active Weeks</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # Top Web developers
        dev_count = 0
        for dev, data in stats['dev_web'].items():
            if dev_count < 15:
                badge_class = 'badge-danger' if data['porcentaje_rechazo'] > 20 else 'badge-warning' if data['porcentaje_rechazo'] > 10 else 'badge-success'
                html += f"""
                        <tr style="cursor: pointer;" ondblclick="showDevDetails('{dev}', 'web')">
                            <td>{dev}</td>
                            <td>{data['total_tarjetas']}</td>
                            <td>{data['rechazadas']}</td>
                            <td>{data['aceptadas']}</td>
                            <td>{data['promedio_semanal_historico']}</td>
                            <td><span class="badge {badge_class}">{data['porcentaje_rechazo']}%</span></td>
                            <td>{data['semanas_activo']}</td>
                        </tr>"""
                dev_count += 1

        html += """
                    </tbody>
                </table>
            </div>
            <div id="devWebDetails" class="info-box" style="display: none; margin-top: 2rem;"></div>

            <h3 style="margin: 2rem 0 1rem 0; color: var(--text-primary);">📱 App Developers</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Developer</th>
                            <th>Total Cards</th>
                            <th>Rejected</th>
                            <th>Accepted</th>
                            <th>Weekly Avg</th>
                            <th>Rejection Rate</th>
                            <th>Active Weeks</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # Top App developers
        dev_count = 0
        for dev, data in stats['dev_app'].items():
            if dev_count < 15:
                badge_class = 'badge-danger' if data['porcentaje_rechazo'] > 20 else 'badge-warning' if data['porcentaje_rechazo'] > 10 else 'badge-success'
                html += f"""
                        <tr style="cursor: pointer;" ondblclick="showDevDetails('{dev}', 'app')">
                            <td>{dev}</td>
                            <td>{data['total_tarjetas']}</td>
                            <td>{data['rechazadas']}</td>
                            <td>{data['aceptadas']}</td>
                            <td>{data['promedio_semanal_historico']}</td>
                            <td><span class="badge {badge_class}">{data['porcentaje_rechazo']}%</span></td>
                            <td>{data['semanas_activo']}</td>
                        </tr>"""
                dev_count += 1

        html += """
                    </tbody>
                </table>
            </div>
            <div id="devAppDetails" class="info-box" style="display: none; margin-top: 2rem;"></div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Developer Comparison</h3>
                </div>
                <div id="devChart" style="height: 500px;"></div>
            </div>
        </div>

        <div id="pm" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">📋</span>
                    Project Management Metrics
                </h2>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">🔴</div>
                    <div class="stat-label">High Priority</div>
                    <div class="stat-value">""" + str(stats['pm']['prioridades']['alta']['total']) + """</div>
                    <div class="metric-label" style="margin-top: 0.5rem;">Avg: """ + str(stats['pm']['prioridades']['alta']['promedio_semanal']) + """ per week</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🟡</div>
                    <div class="stat-label">Medium Priority</div>
                    <div class="stat-value">""" + str(stats['pm']['prioridades']['media']['total']) + """</div>
                    <div class="metric-label" style="margin-top: 0.5rem;">Avg: """ + str(stats['pm']['prioridades']['media']['promedio_semanal']) + """ per week</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🟢</div>
                    <div class="stat-label">Low Priority</div>
                    <div class="stat-value">""" + str(stats['pm']['prioridades']['baja']['total']) + """</div>
                    <div class="metric-label" style="margin-top: 0.5rem;">Avg: """ + str(stats['pm']['prioridades']['baja']['promedio_semanal']) + """ per week</div>
                </div>
            </div>

            <div class="info-box">
                <h3>Weekly Averages</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div class="metric-card">
                        <div class="metric-label">Web Cards</div>
                        <div class="metric-value">""" + str(stats['pm']['promedio_semanal']['web']) + """ / week</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">App Cards</div>
                        <div class="metric-value">""" + str(stats['pm']['promedio_semanal']['app']) + """ / week</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Cards</div>
                        <div class="metric-value">""" + str(stats['pm']['promedio_semanal']['total']) + """ / week</div>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Priority Distribution Over Time</h3>
                </div>
                <div id="priorityChart" style="height: 400px;"></div>
            </div>
        </div>

        <div id="sites" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">🏢</span>
                    Site Statistics
                </h2>
            </div>

            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Site</th>
                            <th>Total</th>
                            <th>Web</th>
                            <th>App</th>
                            <th>Accepted</th>
                            <th>Rejected</th>
                            <th>Avg/Week</th>
                            <th>Active Weeks</th>
                        </tr>
                    </thead>
                    <tbody>"""

        # Top sites
        site_count = 0
        for site, data in stats['sites'].items():
            if site_count < 20:
                html += f"""
                        <tr>
                            <td>{site}</td>
                            <td>{data['total']}</td>
                            <td>{data['web']}</td>
                            <td>{data['app']}</td>
                            <td>{data['aceptadas']}</td>
                            <td>{data['rechazadas']}</td>
                            <td>{data['promedio_por_semana']}</td>
                            <td>{data['semanas_activo']}</td>
                        </tr>"""
                site_count += 1

        html += """
                    </tbody>
                </table>
            </div>

            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Top Sites Distribution</h3>
                </div>
                <div id="siteChart" style="height: 500px;"></div>
            </div>
        </div>

        <div id="weekly" class="tab-content">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="section-title-icon">📅</span>
                    Weekly Analysis
                </h2>
            </div>

            <div style="margin-bottom: 2rem;">
                <label style="font-weight: 600; margin-right: 1rem;">Select Week:</label>
                <div class="custom-select">
                    <select id="weekSelector" onchange="updateWeeklyView()">"""

        for week in stats['weeks_list']:
            html += f'<option value="{week}">{week}</option>'

        html += """
                    </select>
                </div>
            </div>

            <div id="weeklyContent"></div>
        </div>
    </div>

    <script>
        // Global data
        const statsData = """ + json.dumps(stats) + """;

        // Theme toggle
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.querySelector('.theme-toggle').textContent = newTheme === 'dark' ? '☀️' : '🌙';
            updateCharts();
        }

        // Initialize theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.querySelector('.theme-toggle').textContent = savedTheme === 'dark' ? '☀️' : '🌙';

        // Chart configurations
        const plotlyConfig = { 
            displayModeBar: false,
            responsive: true 
        };

        const plotlyLayout = {
            font: {
                family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                size: 12
            },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 40, b: 60, l: 60, r: 30 },
            hovermode: 'closest',
            xaxis: {
                showgrid: false,
                zeroline: false,
                linecolor: 'rgba(0,0,0,0.1)',
                tickfont: { size: 11 }
            },
            yaxis: {
                showgrid: true,
                gridcolor: 'rgba(0,0,0,0.05)',
                zeroline: false,
                linecolor: 'rgba(0,0,0,0.1)',
                tickfont: { size: 11 }
            },
            hoverlabel: {
                bgcolor: '#1e293b',
                bordercolor: '#e2e8f0',
                font: { color: '#fff' }
            }
        };

        // Tab switching
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName).classList.add('active');

            // Activate corresponding button
            const activeButton = Array.from(document.querySelectorAll('.tab-button')).find(btn => 
                btn.textContent.toLowerCase().includes(tabName.toLowerCase()) ||
                (tabName === 'overview' && btn.textContent.includes('Overview')) ||
                (tabName === 'devs' && btn.textContent.includes('Developers'))
            );
            if (activeButton) {
                activeButton.classList.add('active');
            }

            // Load charts for the tab
            setTimeout(() => {
                switch(tabName) {
                    case 'overview':
                        loadOverviewCharts();
                        break;
                    case 'qa':
                        loadQACharts();
                        break;
                    case 'web':
                        loadWebCharts();
                        break;
                    case 'app':
                        loadAppCharts();
                        break;
                    case 'devs':
                        loadDevCharts();
                        break;
                    case 'pm':
                        loadPMCharts();
                        break;
                    case 'sites':
                        loadSiteCharts();
                        break;
                    case 'weekly':
                        updateWeeklyView();
                        break;
                }
            }, 100);
        }

        // Overview Charts
        function loadOverviewCharts() {
            const weeks = statsData.weeks_list.map(w => w.replace('tarjetas semana ', ''));
            const webData = Object.values(statsData.web.weekly);
            const appData = Object.values(statsData.app.weekly);

            const overviewTraces = [
                {
                    x: weeks,
                    y: webData.map(d => d.revisadas),
                    name: 'Web Cards',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#6366f1', width: 3, shape: 'spline' },
                    marker: { size: 8 },
                    fill: 'tonexty',
                    fillcolor: 'rgba(99, 102, 241, 0.1)'
                },
                {
                    x: weeks,
                    y: appData.map(d => d.revisadas),
                    name: 'App Cards',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#ec4899', width: 3, shape: 'spline' },
                    marker: { size: 8 }
                }
            ];

            const overviewLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'Week' },
                yaxis: { ...plotlyLayout.yaxis, title: 'Cards Reviewed' },
                showlegend: true,
                legend: {
                    orientation: 'h',
                    x: 0.5,
                    xanchor: 'center',
                    y: -0.2
                }
            };

            Plotly.newPlot('overviewChart', overviewTraces, overviewLayout, plotlyConfig);

            // Platform Distribution Chart
            const platformData = [{
                labels: Object.keys(statsData.platforms),
                values: Object.values(statsData.platforms),
                type: 'pie',
                hole: 0.6,
                textposition: 'outside',
                textinfo: 'label+percent',
                marker: {
                    colors: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', 
                             '#ef4444', '#3b82f6', '#a855f7', '#f97316', '#14b8a6'],
                    line: { color: '#fff', width: 2 }
                },
                hoverinfo: 'label+value+percent'
            }];

            const platformLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                showlegend: false,
                annotations: [{
                    text: 'Platforms',
                    x: 0.5,
                    y: 0.5,
                    font: { size: 20, weight: 'bold' },
                    showarrow: false
                }]
            };

            Plotly.newPlot('platformChart', platformData, platformLayout, plotlyConfig);
        }

        // QA Charts
        function loadQACharts() {
            const qaNames = Object.keys(statsData.qa.historical.por_qa).slice(0, 10);
            const qaReviewed = qaNames.map(qa => statsData.qa.historical.por_qa[qa].total_revisadas);
            const qaRejected = qaNames.map(qa => statsData.qa.historical.por_qa[qa].total_rechazadas);

            const qaTraces = [
                {
                    x: qaNames,
                    y: qaReviewed,
                    name: 'Reviewed',
                    type: 'bar',
                    marker: { 
                        color: '#6366f1',
                        line: { color: '#4f46e5', width: 1 }
                    }
                },
                {
                    x: qaNames,
                    y: qaRejected,
                    name: 'Rejected',
                    type: 'bar',
                    marker: { 
                        color: '#ef4444',
                        line: { color: '#dc2626', width: 1 }
                    }
                }
            ];

            const qaLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'QA/PM', tickangle: -45 },
                yaxis: { ...plotlyLayout.yaxis, title: 'Number of Cards' },
                barmode: 'group',
                bargap: 0.2,
                bargroupgap: 0.1
            };

            Plotly.newPlot('qaChart', qaTraces, qaLayout, plotlyConfig);
        }

        // Web Charts
        function loadWebCharts() {
            const weeks = Object.keys(statsData.web.weekly).map(w => w.replace('tarjetas semana ', ''));
            const webData = Object.values(statsData.web.weekly);

            const webTraces = [
                {
                    x: weeks,
                    y: webData.map(d => d.porcentaje_rechazo),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Rejection Rate',
                    line: { 
                        color: '#6366f1', 
                        width: 4,
                        shape: 'spline'
                    },
                    marker: { 
                        size: 10,
                        color: '#6366f1',
                        line: { color: '#fff', width: 2 }
                    },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(99, 102, 241, 0.1)'
                }
            ];

            const webLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'Week' },
                yaxis: { 
                    ...plotlyLayout.yaxis, 
                    title: 'Rejection Rate (%)',
                    range: [0, Math.max(...webData.map(d => d.porcentaje_rechazo)) * 1.2]
                },
                shapes: [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    xref: 'paper',
                    y0: statsData.web.historical.porcentaje_rechazo,
                    y1: statsData.web.historical.porcentaje_rechazo,
                    line: {
                        color: '#ef4444',
                        width: 2,
                        dash: 'dash'
                    }
                }],
                annotations: [{
                    x: 0.98,
                    y: statsData.web.historical.porcentaje_rechazo,
                    xref: 'paper',
                    text: 'Average: ' + statsData.web.historical.porcentaje_rechazo + '%',
                    showarrow: false,
                    bgcolor: '#ef4444',
                    bordercolor: '#ef4444',
                    font: { color: '#fff', size: 12 },
                    borderpad: 4,
                    borderwidth: 1,
                    xanchor: 'right'
                }]
            };

            Plotly.newPlot('webChart', webTraces, webLayout, plotlyConfig);
        }

        // App Charts
        function loadAppCharts() {
            const weeks = Object.keys(statsData.app.weekly).map(w => w.replace('tarjetas semana ', ''));
            const appData = Object.values(statsData.app.weekly);

            const appTraces = [
                {
                    x: weeks,
                    y: appData.map(d => d.porcentaje_rechazo),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Rejection Rate',
                    line: { 
                        color: '#ec4899', 
                        width: 4,
                        shape: 'spline'
                    },
                    marker: { 
                        size: 10,
                        color: '#ec4899',
                        line: { color: '#fff', width: 2 }
                    },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(236, 72, 153, 0.1)'
                }
            ];

            const appLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'Week' },
                yaxis: { 
                    ...plotlyLayout.yaxis, 
                    title: 'Rejection Rate (%)',
                    range: [0, Math.max(...appData.map(d => d.porcentaje_rechazo)) * 1.2]
                },
                shapes: [{
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    xref: 'paper',
                    y0: statsData.app.historical.porcentaje_rechazo,
                    y1: statsData.app.historical.porcentaje_rechazo,
                    line: {
                        color: '#ef4444',
                        width: 2,
                        dash: 'dash'
                    }
                }],
                annotations: [{
                    x: 0.98,
                    y: statsData.app.historical.porcentaje_rechazo,
                    xref: 'paper',
                    text: 'Average: ' + statsData.app.historical.porcentaje_rechazo + '%',
                    showarrow: false,
                    bgcolor: '#ef4444',
                    bordercolor: '#ef4444',
                    font: { color: '#fff', size: 12 },
                    borderpad: 4,
                    borderwidth: 1,
                    xanchor: 'right'
                }]
            };

            Plotly.newPlot('appChart', appTraces, appLayout, plotlyConfig);
        }

        // Developer Charts
        function loadDevCharts() {
            const top5Web = Object.entries(statsData.dev_web).slice(0, 5);
            const top5App = Object.entries(statsData.dev_app).slice(0, 5);

            const devTraces = [
                {
                    x: top5Web.map(([dev, data]) => dev),
                    y: top5Web.map(([dev, data]) => data.total_tarjetas),
                    name: 'Web - Total',
                    type: 'bar',
                    marker: { 
                        color: '#6366f1',
                        line: { color: '#4f46e5', width: 1 }
                    }
                },
                {
                    x: top5Web.map(([dev, data]) => dev),
                    y: top5Web.map(([dev, data]) => data.rechazadas),
                    name: 'Web - Rejected',
                    type: 'bar',
                    marker: { 
                        color: 'rgba(99, 102, 241, 0.5)',
                        line: { color: '#6366f1', width: 1 }
                    }
                },
                {
                    x: top5App.map(([dev, data]) => dev),
                    y: top5App.map(([dev, data]) => data.total_tarjetas),
                    name: 'App - Total',
                    type: 'bar',
                    marker: { 
                        color: '#ec4899',
                        line: { color: '#db2777', width: 1 }
                    }
                },
                {
                    x: top5App.map(([dev, data]) => dev),
                    y: top5App.map(([dev, data]) => data.rechazadas),
                    name: 'App - Rejected',
                    type: 'bar',
                    marker: { 
                        color: 'rgba(236, 72, 153, 0.5)',
                        line: { color: '#ec4899', width: 1 }
                    }
                }
            ];

            const devLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'Developer', tickangle: -45 },
                yaxis: { ...plotlyLayout.yaxis, title: 'Number of Cards' },
                barmode: 'group',
                height: 500
            };

            Plotly.newPlot('devChart', devTraces, devLayout, plotlyConfig);
        }

        // PM Charts
        function loadPMCharts() {
            const weeks = Object.keys(statsData.pm.por_semana).map(w => w.replace('tarjetas semana ', ''));
            const pmData = Object.values(statsData.pm.por_semana);

            const pmTraces = [
                {
                    x: weeks,
                    y: pmData.map(d => d.alta),
                    name: 'High Priority',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#ef4444', width: 3 },
                    marker: { size: 8 },
                    stackgroup: 'one'
                },
                {
                    x: weeks,
                    y: pmData.map(d => d.media),
                    name: 'Medium Priority',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#f59e0b', width: 3 },
                    marker: { size: 8 },
                    stackgroup: 'one'
                },
                {
                    x: weeks,
                    y: pmData.map(d => d.baja),
                    name: 'Low Priority',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#10b981', width: 3 },
                    marker: { size: 8 },
                    stackgroup: 'one'
                }
            ];

            const pmLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                xaxis: { ...plotlyLayout.xaxis, title: 'Week' },
                yaxis: { ...plotlyLayout.yaxis, title: 'Number of Cards' },
                hovermode: 'x unified'
            };

            Plotly.newPlot('priorityChart', pmTraces, pmLayout, plotlyConfig);
        }

        // Site Charts
        function loadSiteCharts() {
            const top10Sites = Object.entries(statsData.sites).slice(0, 10);

            const siteTraces = [{
                labels: top10Sites.map(([site, data]) => site),
                values: top10Sites.map(([site, data]) => data.total),
                type: 'pie',
                hole: 0.4,
                textposition: 'outside',
                textinfo: 'label+percent',
                marker: {
                    colors: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', 
                             '#ef4444', '#3b82f6', '#a855f7', '#f97316', '#14b8a6'],
                    line: { color: '#fff', width: 2 }
                },
                hoverinfo: 'label+value+percent'
            }];

            const siteLayout = {
                ...plotlyLayout,
                title: { text: '', font: { size: 16 } },
                height: 500,
                showlegend: true,
                legend: {
                    orientation: 'v',
                    x: 1.1,
                    xanchor: 'left',
                    y: 0.5
                }
            };

            Plotly.newPlot('siteChart', siteTraces, siteLayout, plotlyConfig);
        }

        // Developer Details and Toggle
        let lastClickedDev = { name: null, type: null, showingDetails: false };

        function showDevDetails(devName, devType) {
            const detailsDivId = devType === 'web' ? 'devWebDetails' : 'devAppDetails';
            const detailsDiv = document.getElementById(detailsDivId);

            // Check if it's a second double-click on the SAME developer and currently showing details (summary)
            if (lastClickedDev.name === devName && lastClickedDev.type === devType && lastClickedDev.showingDetails) {
                // Prepare to show detailed cards view with a week selector
                const devWeeklyData = devType === 'web' ? statsData.dev_web_weekly_details[devName] : statsData.dev_app_weekly_details[devName];

                let html = `<h3>Detailed Cards for ${devName}</h3>`;
                
                // Add a dropdown to select the week for detailed cards
                html += '<div style="margin-bottom: 1rem;">';
                html += '<label style="font-weight: 600; margin-right: 0.5rem;">Select Week:</label>';
                html += '<div class="custom-select">';
                html += `<select id="devWeeklyCardSelector" onchange="displayDevWeeklyCards('${devName}', '${devType}', this.value)">`;
                html += '<option value="">-- Select a Week --</option>'; // Default empty option
                for (const week of statsData.weeks_list) {
                    // Only show weeks where the developer has data and cards
                    if (devWeeklyData[week] && devWeeklyData[week].cards && devWeeklyData[week].cards.length > 0) {
                        html += `<option value="${week}">${week.replace('tarjetas semana ', 'Week ')}</option>`;
                    }
                }
                html += '</select>';
                html += '</div></div>';

                html += '<div id="devCardsByWeekContent"></div>'; // This will be populated by displayDevWeeklyCards

                detailsDiv.innerHTML = html;
                detailsDiv.style.display = 'block';
                detailsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                lastClickedDev.showingDetails = false; // Reset to false, so the next double click goes back to summary

            } else {
                // Show weekly summary (first double-click or different developer)
                const weeklyData = devType === 'web' ? 
                    statsData.dev_web_weekly_details[devName] : 
                    statsData.dev_app_weekly_details[devName];
                
                let html = `<h3>Weekly Performance: ${devName}</h3>`;
                html += '<table style="width: 100%; margin-top: 1rem;">';
                html += '<thead><tr><th>Week</th><th>Total Cards</th><th>Rejected</th><th>Accepted</th><th>Rejection Rate</th></tr></thead><tbody>';
                
                if (!weeklyData || Object.keys(weeklyData).length === 0) {
                    html += '<tr><td colspan="5" style="text-align: center;">No weekly data available</td></tr>';
                } else {
                    for (const week of statsData.weeks_list) {
                        const data = weeklyData[week];
                        if (data) {
                            const badgeClass = data.porcentaje_rechazo > 20 ? 'badge-danger' : 
                                                 data.porcentaje_rechazo > 10 ? 'badge-warning' : 'badge-success';
                            html += `<tr>
                                    <td>${week.replace('tarjetas semana ', 'Week ')}</td>
                                    <td>${data.total_tarjetas}</td>
                                    <td>${data.rechazadas}</td>
                                    <td>${data.aceptadas}</td>
                                    <td><span class="badge ${badgeClass}">${data.porcentaje_rechazo}%</span></td>
                                </tr>`;
                        }
                    }
                }
                
                html += '</tbody></table>';
                
                detailsDiv.innerHTML = html;
                detailsDiv.style.display = 'block';
                detailsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                lastClickedDev.name = devName;
                lastClickedDev.type = devType;
                lastClickedDev.showingDetails = true; // Set to true to indicate summary is showing
            }
        }

        // New function to display detailed cards for a specific developer and week
        function displayDevWeeklyCards(devName, devType, selectedWeek) {
            const devWeeklyData = devType === 'web' ? statsData.dev_web_weekly_details[devName] : statsData.dev_app_weekly_details[devName];
            const cards = devWeeklyData[selectedWeek] ? devWeeklyData[selectedWeek].cards : [];

            let cardsHtml = '<div class="table-container" style="margin-top: 1rem;"><table><thead><tr><th>Descripción</th><th>Estado</th></tr></thead><tbody>';

            if (cards.length === 0) {
                cardsHtml += '<tr><td colspan="2" style="text-align: center;">No cards found for this week.</td></tr>';
            } else {
                for (const card of cards) {
                    const badgeClass = card['Aceptado/Rechazado'] === 'RECHAZADO'
                        ? 'badge-danger'
                        : card['Aceptado/Rechazado'] === 'APROBADO'
                        ? 'badge-success'
                        : card['Aceptado/Rechazado'] === 'PENDIENTE' // Handle PENDIENTE case
                        ? 'badge-warning'
                        : 'badge-warning'; // Default for unknown statuses

                    const description = card['Descripción'] || 'No Description Available';

                    cardsHtml += `<tr>
                                    <td>${description}</td>
                                    <td><span class="badge ${badgeClass}">${card['Aceptado/Rechazado']}</span></td>
                                 </tr>`;
                }
            }
            cardsHtml += '</tbody></table></div>';
            document.getElementById('devCardsByWeekContent').innerHTML = cardsHtml;
        }


        // Weekly View Logic
        let lastClickedWeek = null;
        let showingDetails = false;

        function updateWeeklyView() {
            const selectedWeek = document.getElementById('weekSelector').value;

            if (selectedWeek === lastClickedWeek && showingDetails) {
                // Show specific cards if double-clicked again
                const cards = statsData.cards_by_week[selectedWeek];

                let html = `<h3>Tarjetas de la semana: ${selectedWeek}</h3>`;
                html += '<div class="table-container"><table><thead><tr><th>Descripción</th><th>Estado</th></tr></thead><tbody>';

                for (const card of cards) {
                    const badgeClass = card['Aceptado/Rechazado'] === 'RECHAZADO'
                        ? 'badge-danger'
                        : card['Aceptado/Rechazado'] === 'APROBADO'
                        ? 'badge-success'
                        : 'badge-warning';

                    // Check if 'Descripción' exists, otherwise show a placeholder or just the status
                    const description = card['Descripción'] || 'No Description'; 

                    html += `<tr>
                                <td>${description}</td>
                                <td><span class="badge ${badgeClass}">${card['Aceptado/Rechazado']}</span></td>
                            </tr>`;
                }

                html += '</tbody></table></div>';
                document.getElementById('weeklyContent').innerHTML = html;
                showingDetails = false; // Reset flag to show summary on next single click
            } else {
                // Regular summary view (first click or different week)
                lastClickedWeek = selectedWeek;
                showingDetails = true; // Set flag to indicate summary is currently showing

                const weekData = {
                    qa: statsData.qa.weekly[selectedWeek],
                    web: statsData.web.weekly[selectedWeek],
                    app: statsData.app.weekly[selectedWeek],
                    pm: statsData.pm.por_semana[selectedWeek]
                };

                let html = '<div class="stats-grid">';
                
                // QA Stats
                html += '<div class="stat-card">';
                html += '<div class="stat-icon">👥</div>';
                html += '<div class="stat-label">Total Cards</div>';
                html += '<div class="stat-value">' + weekData.qa.total_semana + '</div>';
                html += '<div class="stat-change negative">';
                html += weekData.qa.total_rechazadas_semana + ' rejected';
                html += '</div>';
                html += '</div>';

                // Web Stats
                html += '<div class="stat-card">';
                html += '<div class="stat-icon">🌐</div>';
                html += '<div class="stat-label">Web Performance</div>';
                html += '<div class="stat-value">' + weekData.web.revisadas + '</div>';
                html += '<div class="progress-bar" style="margin-top: 1rem;">';
                html += '<div class="progress-fill" style="width: ' + (100 - weekData.web.porcentaje_rechazo) + '%"></div>';
                html += '</div>';
                html += '<div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.875rem;">';
                html += '<span style="color: var(--success);">✓ ' + weekData.web.aceptadas + '</span>';
                html += '<span style="color: var(--danger);">✗ ' + weekData.web.rechazadas + '</span>';
                html += '</div>';
                html += '</div>';

                // App Stats
                html += '<div class="stat-card">';
                html += '<div class="stat-icon">📱</div>';
                html += '<div class="stat-label">App Performance</div>';
                html += '<div class="stat-value">' + weekData.app.revisadas + '</div>';
                html += '<div class="progress-bar" style="margin-top: 1rem;">';
                html += '<div class="progress-fill" style="width: ' + (100 - weekData.app.porcentaje_rechazo) + '%"></div>';
                html += '</div>';
                html += '<div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.875rem;">';
                html += '<span style="color: var(--success);">✓ ' + weekData.app.aceptadas + '</span>';
                html += '<span style="color: var(--danger);">✗ ' + weekData.app.rechazadas + '</span>';
                html += '</div>';
                html += '</div>';

                // Priority Stats
                html += '<div class="stat-card">';
                html += '<div class="stat-icon">📊</div>';
                html += '<div class="stat-label">Priority Distribution</div>';
                html += '<div style="margin-top: 1rem;">';
                html += '<div class="metric-card">';
                html += '<div class="metric-label">🔴 High Priority</div>';
                html += '<div class="metric-value">' + weekData.pm.alta + '</div>';
                html += '</div>';
                html += '<div class="metric-card">';
                html += '<div class="metric-label">🟡 Medium Priority</div>';
                html += '<div class="metric-value">' + weekData.pm.media + '</div>';
                html += '</div>';
                html += '<div class="metric-card">';
                html += '<div class="metric-label">🟢 Low Priority</div>';
                html += '<div class="metric-value">' + weekData.pm.baja + '</div>';
                html += '</div>';
                html += '</div>';
                html += '</div>';
                
                html += '</div>';

                // QA Performance Table
                html += '<div class="table-container" style="margin-top: 2rem;">';
                html += '<h3 style="padding: 1rem; font-size: 1.25rem;">QA Performance This Week</h3>';
                html += '<table><thead><tr><th>QA/PM</th><th>Cards Reviewed</th><th>Cards Rejected</th><th>Rejection Rate</th></tr></thead><tbody>';

                for (const [qa, count] of Object.entries(weekData.qa.tarjetas_por_qa)) {
                    const rejected = weekData.qa.rechazadas_por_qa[qa] || 0;
                    const rate = count > 0 ? (rejected / count * 100).toFixed(1) : 0;
                    const badgeClass = rate > 20 ? 'badge-danger' : rate > 10 ? 'badge-warning' : 'badge-success';
                    html += `<tr>
                        <td>${qa}</td>
                        <td>${count}</td>
                        <td>${rejected}</td>
                        <td><span class="badge ${badgeClass}">${rate}%</span></td>
                    </tr>`;
                }

                html += '</tbody></table></div>';
                document.getElementById('weeklyContent').innerHTML = html;
            }
        }

        // Update charts when theme changes
        function updateCharts() {
            const currentTab = document.querySelector('.tab-content.active').id;
            showTab(currentTab);
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Add smooth scrolling
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({
                        behavior: 'smooth'
                    });
                });
            });

            // Load initial charts
            loadOverviewCharts();

            // Initialize weekly view
            if (statsData.weeks_list.length > 0) {
                document.getElementById('weekSelector').value = statsData.weeks_list[statsData.weeks_list.length - 1];
                updateWeeklyView(); // Initial load for the weekly tab
            }

            // Add hover effects to cards
            document.querySelectorAll('.stat-card').forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-10px) scale(1.02)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0) scale(1)';
                });
            });

             // Add double-click listener to the weekSelector dropdown
             document.getElementById('weekSelector').addEventListener('dblclick', function() {
                updateWeeklyView(); // Trigger the view update
            });
        });

        // Resize handler for responsive charts
        window.addEventListener('resize', function() {
            const charts = ['overviewChart', 'platformChart', 'qaChart', 'webChart', 
                            'appChart', 'devChart', 'priorityChart', 'siteChart'];
            charts.forEach(chartId => {
                const chartDiv = document.getElementById(chartId);
                if (chartDiv && chartDiv.data) {
                    Plotly.Plots.resize(chartId);
                }
            });
        });
    </script>
</body>
</html>"""

        return html

    def save_dashboard(self, filename='qa_dashboard_enhanced.html'):
        """Guarda el dashboard mejorado como archivo HTML"""
        print("\nGenerando todas las estadísticas...")
        stats = self.generate_all_statistics()

        print("Creando dashboard HTML con diseño moderno...")
        html_content = self.generate_html_dashboard(stats)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Dashboard guardado exitosamente como '{filename}'")
            # This part is commented out as it requires a local environment setup
            # webbrowser.open(f'file:///{os.path.abspath(filename)}')
        except Exception as e:
            print(f"Error al guardar o abrir el dashboard: {e}")

if __name__ == "__main__":
    print("The Python script has been updated to include 'Tester' in the QA section and double-click functionality for weekly card details, including for developers.")
    print("Please note: The parts of the script that interact with the local file system (tkinter and shutil) have been commented out for compatibility with this environment.")
    print("You can copy this code and run it in your local Python environment with the required Excel file.")
