# Create DB
CREATE DATABASE IF NOT EXISTS django;

# Create Schema - generated from current impl

CREATE SCHEMA IF NOT EXISTS `django` DEFAULT CHARACTER SET utf8 ;
USE `django` ;
-- -----------------------------------------------------
-- Table `django`.`auth_group`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`auth_group` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(80) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `name` (`name` ASC) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`django_content_type`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`django_content_type` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(100) NOT NULL ,
  `app_label` VARCHAR(100) NOT NULL ,
  `model` VARCHAR(100) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `django_content_type_app_label_3ec8c61c_uniq` (`app_label` ASC, `model` ASC) )

ENGINE = InnoDB
AUTO_INCREMENT = 22
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`auth_permission`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`auth_permission` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(50) NOT NULL ,
  `content_type_id` INT(11) NOT NULL ,
  `codename` VARCHAR(100) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `content_type_id` (`content_type_id` ASC, `codename` ASC) ,
  INDEX `auth_permission_417f1b1c` (`content_type_id` ASC) ,
  CONSTRAINT `auth_permissi_content_type_id_51277a81_fk_django_content_type_id`
    FOREIGN KEY (`content_type_id` )
    REFERENCES `django`.`django_content_type` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 64
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`auth_group_permissions`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`auth_group_permissions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `group_id` INT(11) NOT NULL ,
  `permission_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `group_id` (`group_id` ASC, `permission_id` ASC) ,
  INDEX `auth_group_permissions_0e939a4f` (`group_id` ASC) ,
  INDEX `auth_group_permissions_8373b171` (`permission_id` ASC) ,
  CONSTRAINT `auth_group_permissi_permission_id_23962d04_fk_auth_permission_id`
    FOREIGN KEY (`permission_id` )
    REFERENCES `django`.`auth_permission` (`id` ),
  CONSTRAINT `auth_group_permissions_group_id_58c48ba9_fk_auth_group_id`
    FOREIGN KEY (`group_id` )
    REFERENCES `django`.`auth_group` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`auth_user`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`auth_user` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `password` VARCHAR(128) NOT NULL ,
  `last_login` DATETIME NOT NULL ,
  `is_superuser` TINYINT(1) NOT NULL ,
  `username` VARCHAR(30) NOT NULL ,
  `first_name` VARCHAR(30) NOT NULL ,
  `last_name` VARCHAR(30) NOT NULL ,
  `email` VARCHAR(75) NOT NULL ,
  `is_staff` TINYINT(1) NOT NULL ,
  `is_active` TINYINT(1) NOT NULL ,
  `date_joined` DATETIME NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `username` (`username` ASC) )

ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`auth_user_groups`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `django`.`auth_user_groups` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `user_id` INT(11) NOT NULL ,
  `group_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `user_id` (`user_id` ASC, `group_id` ASC) ,
  INDEX `auth_user_groups_e8701ad4` (`user_id` ASC) ,
  INDEX `auth_user_groups_0e939a4f` (`group_id` ASC) ,
  CONSTRAINT `auth_user_groups_group_id_30a071c9_fk_auth_group_id`
    FOREIGN KEY (`group_id` )
    REFERENCES `django`.`auth_group` (`id` ),
  CONSTRAINT `auth_user_groups_user_id_24702650_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `django`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`auth_user_user_permissions`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `django`.`auth_user_user_permissions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `user_id` INT(11) NOT NULL ,
  `permission_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `user_id` (`user_id` ASC, `permission_id` ASC) ,
  INDEX `auth_user_user_permissions_e8701ad4` (`user_id` ASC) ,
  INDEX `auth_user_user_permissions_8373b171` (`permission_id` ASC) ,
  CONSTRAINT `auth_user_user_perm_permission_id_3d7071f0_fk_auth_permission_id`
    FOREIGN KEY (`permission_id` )
    REFERENCES `django`.`auth_permission` (`id` ),
  CONSTRAINT `auth_user_user_permissions_user_id_7cd7acb6_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `django`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`django_admin_log`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `django`.`django_admin_log` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `action_time` DATETIME NOT NULL ,
  `object_id` LONGTEXT NULL DEFAULT NULL ,
  `object_repr` VARCHAR(200) NOT NULL ,
  `action_flag` SMALLINT(5) UNSIGNED NOT NULL ,
  `change_message` LONGTEXT NOT NULL ,
  `content_type_id` INT(11) NULL DEFAULT NULL ,
  `user_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `django_admin_log_417f1b1c` (`content_type_id` ASC) ,
  INDEX `django_admin_log_e8701ad4` (`user_id` ASC) ,
  CONSTRAINT `django_admin__content_type_id_5151027a_fk_django_content_type_id`
    FOREIGN KEY (`content_type_id` )
    REFERENCES `django`.`django_content_type` (`id` ),
  CONSTRAINT `django_admin_log_user_id_1c5f563_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `django`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`django_migrations`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `django`.`django_migrations` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `app` VARCHAR(255) NOT NULL ,
  `name` VARCHAR(255) NOT NULL ,
  `applied` DATETIME NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `django`.`django_session`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `django`.`django_session` (
  `session_key` VARCHAR(40) NOT NULL ,
  `session_data` LONGTEXT NOT NULL ,
  `expire_date` DATETIME NOT NULL ,
  PRIMARY KEY (`session_key`) ,
  INDEX `django_session_de54fa62` (`expire_date` ASC) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;
