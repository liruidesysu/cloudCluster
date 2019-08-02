# -*- encoding: utf-8 -*-
# Copyright 2016 Vinzor Co.,Ltd.
#
# comment
#
# 8/2/19 liruide : Init
import datetime
from datetime import timedelta
import json
import time
import copy
import traceback
import functools
from collections import defaultdict
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin
from flask.ext.sqlalchemy import BaseQuery
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import case, desc
from sqlalchemy.orm import relationship
from . import login_manager
from . import db
from .common import network_utils, password_utils
from phoenix.cloud import compute
from phoenix.cloud import image
from influxdb import InfluxDBClient

##################
# auth
##################

class Permission:
    COURSE = 0x01
    DESKTOP = 0x02
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_default_roles():
        roles = {
            'Administrator': {
                'permissions': (0x80),
                'description': 'administrator'
            },
            'Teacher': {
                'permissions': (Permission.COURSE | Permission.DESKTOP),
                'description': 'teacher role'
            },
            'Student': {
                'permissions': (Permission.DESKTOP),
                'description': 'student role'
            },
            'Terminal': {
                'permissions': (Permission.DESKTOP),
                'description': 'terminal role'
            }
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r]['permissions']
            role.description = roles[r]['description']
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class UserStatus(object):
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    fullname = db.Column(db.String(64), default="")
    email = db.Column(db.String(64), unique=True, index=True)
    is_active = db.Column(db.Boolean, default=True)
    is_device = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=True)

    terminal = relationship("Terminal", uselist=False, back_populates="user")
    desktops = db.relationship('Desktop', backref='owner')
    own_courses = db.relationship('Course', backref='owner', lazy='dynamic')
    ftp_accounts = db.relationship('FtpAccount', backref='owner', cascade="all, delete-orphan", lazy='dynamic')
    personal_storage_accounts = db.relationship('PersonalStorageAccount', backref='user', cascade="all, delete-orphan", lazy='dynamic')
    images = db.relationship('Image', backref='user', lazy='dynamic')

    image_number = db.Column(db.Integer, default=9999)

    # permissions = 0xff

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def can(self, permissions):
        return self.role.permissions & permissions == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_super_administrator(self):
        return self.username == 'admin'

    def gravatar(self, size=100, default='identicon', rating='g'):
        return ''

    def generate_reset_password_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'reset': self.email})

    def reset_password(self, token, password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception as e:
            return False
        if data.get('reset') != self.email:
            return False
        self.password = password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    def __repr__(self):
        return '<User %r>' % self.username

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def get_desktop(self, desktop_id):
        for desktop in self.desktops:
            if desktop.id == desktop_id:
                return desktop
        return None

    @staticmethod
    def insert_default_users():
        users = {
            'admin': {
                'email': 'admin@example.com',
                'password': 'admin123',
                'role': 'Administrator',
            },
            'teacher': {
                'email': 'teacher@example.com',
                'password': 'admin123',
                'role': 'Teacher',
            },
            'student': {
                'email': 'student@example.com',
                'password': 'admin123',
                'role': 'Student',
            }
        }
        for u in users:
            user = User.query.filter_by(username=u).first()
            if user is None:
                user = User(username=u, fullname=u, email=users[u]['email'], is_active=True, confirmed=True)
                user.password = users[u]['password']
                user.role = Role.query.filter_by(name=users[u]['role']).first()
            db.session.add(user)
        db.session.commit()
