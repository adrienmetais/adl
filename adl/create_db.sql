create table users (
  user_id text,
  sign_id text,
  sign_method text,
  auth_pub text,
  auth_priv text,
  license_pub text,
  license_priv text,
  pkcs12 text,
  eplk text,
  license_certificate text
);

create table devices (
  user_id text,
  device_key text,
  device_id text);
