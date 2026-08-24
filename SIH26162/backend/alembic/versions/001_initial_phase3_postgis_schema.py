"""
Initial Phase 3 PostgreSQL + PostGIS Schema.

Revision ID: 001_initial_phase3
Revises: 
Create Date: 2026-08-24 19:10:00.000000

Creates tables:
- firms_observations
- persistent_thermal_sources
- thermal_classifications
- risk_assessments
- industrial_facilities
- ml_model_metadata

Along with PostGIS extension, GiST spatial indexes, B-tree indexes, and foreign key constraints.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '001_initial_phase3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS Extension if on PostgreSQL
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. industrial_facilities table
    op.create_table(
        'industrial_facilities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('osm_id', sa.BigInteger(), nullable=True),
        sa.Column('osm_type', sa.String(length=20), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('facility_type', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('osm_id', name='uq_facility_osm_id'),
    )
    op.create_index('idx_facility_lat_lon', 'industrial_facilities', ['latitude', 'longitude'])
    op.create_index('idx_facility_type', 'industrial_facilities', ['facility_type'])

    # 3. persistent_thermal_sources table
    op.create_table(
        'persistent_thermal_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('centroid_lat', sa.Float(), nullable=False),
        sa.Column('centroid_lon', sa.Float(), nullable=False),
        sa.Column('centroid_geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('first_seen_utc', sa.DateTime(), nullable=False),
        sa.Column('last_seen_utc', sa.DateTime(), nullable=False),
        sa.Column('persistence_duration_days', sa.Float(), nullable=False),
        sa.Column('mean_frp_mw', sa.Float(), nullable=False),
        sa.Column('max_frp_mw', sa.Float(), nullable=False),
        sa.Column('mean_brightness_kelvin', sa.Float(), nullable=False),
        sa.Column('mean_confidence', sa.Float(), nullable=False),
        sa.Column('night_observation_ratio', sa.Float(), nullable=False),
        sa.Column('spatial_radius_meters', sa.Float(), nullable=False),
        sa.Column('is_persistent', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('nearest_industrial_facility_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['nearest_industrial_facility_id'], ['industrial_facilities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cluster_id', name='uq_thermal_source_cluster_id'),
    )
    op.create_index('idx_thermal_source_centroid', 'persistent_thermal_sources', ['centroid_lat', 'centroid_lon'])
    op.create_index('idx_thermal_source_obs_count', 'persistent_thermal_sources', ['observation_count'])
    op.create_index('idx_thermal_source_persistence', 'persistent_thermal_sources', ['is_persistent'])

    # 4. firms_observations table
    op.create_table(
        'firms_observations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('brightness_primary', sa.Float(), nullable=False),
        sa.Column('brightness_secondary', sa.Float(), nullable=True),
        sa.Column('frp', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('confidence_category', sa.String(length=20), nullable=False, server_default='nominal'),
        sa.Column('acq_datetime', sa.DateTime(), nullable=False),
        sa.Column('satellite', sa.String(length=50), nullable=False),
        sa.Column('instrument', sa.String(length=50), nullable=False),
        sa.Column('daynight', sa.String(length=10), nullable=False, server_default='D'),
        sa.Column('scan', sa.Float(), nullable=False, server_default='0.375'),
        sa.Column('track', sa.Float(), nullable=False, server_default='0.375'),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('latitude', 'longitude', 'acq_datetime', 'satellite', 'instrument', name='uq_firms_observation_pass'),
    )
    op.create_index('idx_firms_coords_datetime', 'firms_observations', ['latitude', 'longitude', 'acq_datetime'])
    op.create_index('idx_firms_frp_conf', 'firms_observations', ['frp', 'confidence_score'])
    op.create_index('idx_firms_cluster_id', 'firms_observations', ['cluster_id'])
    op.create_index('idx_firms_acq_datetime', 'firms_observations', ['acq_datetime'])
    op.create_index('idx_firms_satellite', 'firms_observations', ['satellite'])

    # 5. thermal_classifications table
    op.create_table(
        'thermal_classifications',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_id', sa.BigInteger(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('predicted_class', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('class_probabilities', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False, server_default='random_forest_v1'),
        sa.Column('is_weak_label', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_id'], ['firms_observations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_classification_class_conf', 'thermal_classifications', ['predicted_class', 'confidence'])
    op.create_index('idx_classification_coords', 'thermal_classifications', ['latitude', 'longitude'])
    op.create_index('idx_classification_obs_id', 'thermal_classifications', ['observation_id'])

    # 6. risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('classification_id', sa.BigInteger(), nullable=True),
        sa.Column('observation_id', sa.BigInteger(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('frp_subscore', sa.Float(), nullable=False),
        sa.Column('industrial_proximity_subscore', sa.Float(), nullable=False),
        sa.Column('persistence_subscore', sa.Float(), nullable=False),
        sa.Column('confidence_subscore', sa.Float(), nullable=False),
        sa.Column('nocturnal_subscore', sa.Float(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['classification_id'], ['thermal_classifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['observation_id'], ['firms_observations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_risk_level_score', 'risk_assessments', ['risk_level', 'risk_score'])
    op.create_index('idx_risk_assessment_clf_id', 'risk_assessments', ['classification_id'])
    op.create_index('idx_risk_assessment_obs_id', 'risk_assessments', ['observation_id'])

    # 7. ml_model_metadata table
    op.create_table(
        'ml_model_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('dataset_size', sa.Integer(), nullable=False),
        sa.Column('train_accuracy', sa.Float(), nullable=False),
        sa.Column('test_accuracy', sa.Float(), nullable=False),
        sa.Column('test_f1_macro', sa.Float(), nullable=False),
        sa.Column('test_roc_auc', sa.Float(), nullable=True),
        sa.Column('features_used', sa.JSON(), nullable=False),
        sa.Column('artifact_path', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version', name='uq_model_version'),
    )
    op.create_index('idx_model_type_version', 'ml_model_metadata', ['model_type', 'version'])


def downgrade() -> None:
    op.drop_table('ml_model_metadata')
    op.drop_table('risk_assessments')
    op.drop_table('thermal_classifications')
    op.drop_table('firms_observations')
    op.drop_table('persistent_thermal_sources')
    op.drop_table('industrial_facilities')
