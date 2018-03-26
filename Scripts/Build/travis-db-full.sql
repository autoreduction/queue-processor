# Create Test user
CREATE USER 'test-user'@'localhost' IDENTIFIED BY 'pass';
GRANT ALL ON autoreduction.* TO 'test-user'@'localhost';

# Create DB
CREATE DATABASE IF NOT EXISTS autoreduction;

# Create Schema - generated from current impl

CREATE SCHEMA IF NOT EXISTS `autoreduction` DEFAULT CHARACTER SET utf8 ;
USE `autoreduction` ;
-- -----------------------------------------------------
-- Table `autoreduction`.`auth_group`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_group` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(80) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `name` (`name` ASC) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`django_content_type`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`django_content_type` (
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
-- Table `autoreduction`.`auth_permission`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_permission` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(50) NOT NULL ,
  `content_type_id` INT(11) NOT NULL ,
  `codename` VARCHAR(100) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `content_type_id` (`content_type_id` ASC, `codename` ASC) ,
  INDEX `auth_permission_417f1b1c` (`content_type_id` ASC) ,
  CONSTRAINT `auth_permissi_content_type_id_51277a81_fk_django_content_type_id`
    FOREIGN KEY (`content_type_id` )
    REFERENCES `autoreduction`.`django_content_type` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 64
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`auth_group_permissions`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_group_permissions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `group_id` INT(11) NOT NULL ,
  `permission_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `group_id` (`group_id` ASC, `permission_id` ASC) ,
  INDEX `auth_group_permissions_0e939a4f` (`group_id` ASC) ,
  INDEX `auth_group_permissions_8373b171` (`permission_id` ASC) ,
  CONSTRAINT `auth_group_permissi_permission_id_23962d04_fk_auth_permission_id`
    FOREIGN KEY (`permission_id` )
    REFERENCES `autoreduction`.`auth_permission` (`id` ),
  CONSTRAINT `auth_group_permissions_group_id_58c48ba9_fk_auth_group_id`
    FOREIGN KEY (`group_id` )
    REFERENCES `autoreduction`.`auth_group` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`auth_user`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_user` (
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
-- Table `autoreduction`.`auth_user_groups`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_user_groups` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `user_id` INT(11) NOT NULL ,
  `group_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `user_id` (`user_id` ASC, `group_id` ASC) ,
  INDEX `auth_user_groups_e8701ad4` (`user_id` ASC) ,
  INDEX `auth_user_groups_0e939a4f` (`group_id` ASC) ,
  CONSTRAINT `auth_user_groups_group_id_30a071c9_fk_auth_group_id`
    FOREIGN KEY (`group_id` )
    REFERENCES `autoreduction`.`auth_group` (`id` ),
  CONSTRAINT `auth_user_groups_user_id_24702650_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `autoreduction`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`auth_user_user_permissions`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`auth_user_user_permissions` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `user_id` INT(11) NOT NULL ,
  `permission_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `user_id` (`user_id` ASC, `permission_id` ASC) ,
  INDEX `auth_user_user_permissions_e8701ad4` (`user_id` ASC) ,
  INDEX `auth_user_user_permissions_8373b171` (`permission_id` ASC) ,
  CONSTRAINT `auth_user_user_perm_permission_id_3d7071f0_fk_auth_permission_id`
    FOREIGN KEY (`permission_id` )
    REFERENCES `autoreduction`.`auth_permission` (`id` ),
  CONSTRAINT `auth_user_user_permissions_user_id_7cd7acb6_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `autoreduction`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`autoreduce_webapp_cache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`autoreduce_webapp_cache` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `created` DATETIME NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`autoreduce_webapp_experimentcache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`autoreduce_webapp_experimentcache` (
  `cache_ptr_id` INT(11) NOT NULL ,
  `id_name` INT(11) NOT NULL ,
  `start_date` LONGTEXT NOT NULL ,
  `end_date` LONGTEXT NOT NULL ,
  `title` LONGTEXT NOT NULL ,
  `summary` LONGTEXT NOT NULL ,
  `instrument` LONGTEXT NOT NULL ,
  `pi` LONGTEXT NOT NULL ,
  PRIMARY KEY (`cache_ptr_id`) ,
  CONSTRAINT `cache_ptr_id_refs_id_ed818ea9`
    FOREIGN KEY (`cache_ptr_id` )
    REFERENCES `autoreduction`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`autoreduce_webapp_instrumentcache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`autoreduce_webapp_instrumentcache` (
  `cache_ptr_id` INT(11) NOT NULL ,
  `id_name` VARCHAR(80) NOT NULL ,
  `upcoming_experiments` LONGTEXT NOT NULL ,
  `valid_experiments` LONGTEXT NOT NULL ,
  PRIMARY KEY (`cache_ptr_id`) ,
  CONSTRAINT `cache_ptr_id_refs_id_6d7bc58e`
    FOREIGN KEY (`cache_ptr_id` )
    REFERENCES `autoreduction`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`autoreduce_webapp_usercache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`autoreduce_webapp_usercache` (
  `cache_ptr_id` INT(11) NOT NULL ,
  `id_name` INT(11) NOT NULL ,
  `associated_experiments` LONGTEXT NOT NULL ,
  `owned_instruments` LONGTEXT NOT NULL ,
  `valid_instruments` LONGTEXT NOT NULL ,
  `is_admin` TINYINT(1) NOT NULL ,
  `is_instrument_scientist` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`cache_ptr_id`) ,
  CONSTRAINT `cache_ptr_id_refs_id_2d335368`
    FOREIGN KEY (`cache_ptr_id` )
    REFERENCES `autoreduction`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`django_admin_log`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `autoreduction`.`django_admin_log` (
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
    REFERENCES `autoreduction`.`django_content_type` (`id` ),
  CONSTRAINT `django_admin_log_user_id_1c5f563_fk_auth_user_id`
    FOREIGN KEY (`user_id` )
    REFERENCES `autoreduction`.`auth_user` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`django_migrations`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `autoreduction`.`django_migrations` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `app` VARCHAR(255) NOT NULL ,
  `name` VARCHAR(255) NOT NULL ,
  `applied` DATETIME NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 5
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`django_session`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `autoreduction`.`django_session` (
  `session_key` VARCHAR(40) NOT NULL ,
  `session_data` LONGTEXT NOT NULL ,
  `expire_date` DATETIME NOT NULL ,
  PRIMARY KEY (`session_key`) ,
  INDEX `django_session_de54fa62` (`expire_date` ASC) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_instrument`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_instrument` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(80) NOT NULL ,
  `is_active` TINYINT(1) NOT NULL ,
  `is_paused` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `idx_reduction_viewer_instrument_name` (`name` ASC) )

ENGINE = InnoDB
AUTO_INCREMENT = 10
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_variables_variable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_variables_variable` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(50) NOT NULL ,
  `value` VARCHAR(300) NOT NULL ,
  `type` VARCHAR(50) NOT NULL ,
  `is_advanced` TINYINT(1) NOT NULL ,
  `help_text` LONGTEXT NULL DEFAULT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 5452
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_variables_instrumentvariable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_variables_instrumentvariable` (
  `variable_ptr_id` INT(11) NOT NULL ,
  `instrument_id` INT(11) NOT NULL ,
  `experiment_reference` INT(11) NULL DEFAULT NULL ,
  `start_run` INT(11) NULL DEFAULT NULL ,
  `tracks_script` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`variable_ptr_id`) ,
  INDEX `reduction_variables_instrumentvariable_ce1084cd` (`instrument_id` ASC) ,
  CONSTRAINT `instrument_id_refs_id_b848104d`
    FOREIGN KEY (`instrument_id` )
    REFERENCES `autoreduction`.`reduction_viewer_instrument` (`id` ),
  CONSTRAINT `variable_ptr_id_refs_id_a230c877`
    FOREIGN KEY (`variable_ptr_id` )
    REFERENCES `autoreduction`.`reduction_variables_variable` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_experiment`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_experiment` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `reference_number` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_status`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_status` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `value` VARCHAR(25) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_reductionrun`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_reductionrun` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `run_number` INT(11) NOT NULL ,
  `run_version` INT(11) NOT NULL ,
  `run_name` VARCHAR(200) NOT NULL ,
  `experiment_id` INT(11) NOT NULL ,
  `instrument_id` INT(11) NULL DEFAULT NULL ,
  `script` LONGTEXT NOT NULL ,
  `status_id` INT(11) NOT NULL ,
  `created` DATETIME NOT NULL ,
  `last_updated` DATETIME NOT NULL ,
  `started` DATETIME NULL DEFAULT NULL ,
  `finished` DATETIME NULL DEFAULT NULL ,
  `started_by` INT(11) NULL DEFAULT NULL ,
  `graph` LONGTEXT NULL DEFAULT NULL ,
  `message` LONGTEXT NOT NULL ,
  `reduction_log` LONGTEXT NOT NULL ,
  `admin_log` LONGTEXT NOT NULL ,
  `retry_run_id` INT(11) NULL DEFAULT NULL ,
  `retry_when` DATETIME NULL DEFAULT NULL ,
  `cancel` TINYINT(1) NOT NULL ,
  `hidden_in_failviewer` TINYINT(1) NOT NULL ,
  `overwrite` TINYINT(1) NULL DEFAULT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `reduction_viewer_reductionrun_3e8130cb` (`experiment_id` ASC) ,
  INDEX `reduction_viewer_reductionrun_ce1084cd` (`instrument_id` ASC) ,
  INDEX `reduction_viewer_reductionrun_48fb58bb` (`status_id` ASC) ,
  INDEX `reduction_viewer_reductionrun_ec4db0a4` (`retry_run_id` ASC) ,
  INDEX `test` (`instrument_id` ASC, `run_version` ASC, `run_number` ASC, `run_name` ASC, `status_id` ASC) ,
  CONSTRAINT `experiment_id_refs_id_daaf2f61`
    FOREIGN KEY (`experiment_id` )
    REFERENCES `autoreduction`.`reduction_viewer_experiment` (`id` ),
  CONSTRAINT `instrument_id_refs_id_978dd513`
    FOREIGN KEY (`instrument_id` )
    REFERENCES `autoreduction`.`reduction_viewer_instrument` (`id` ),
  CONSTRAINT `retry_run_id_refs_id_a07852ad`
    FOREIGN KEY (`retry_run_id` )
    REFERENCES `autoreduction`.`reduction_viewer_reductionrun` (`id` ),
  CONSTRAINT `status_id_refs_id_f353ac8f`
    FOREIGN KEY (`status_id` )
    REFERENCES `autoreduction`.`reduction_viewer_status` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 492
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_variables_runvariable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_variables_runvariable` (
  `variable_ptr_id` INT(11) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`variable_ptr_id`) ,
  INDEX `reduction_variables_runvariable_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_7a2c2892`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `autoreduction`.`reduction_viewer_reductionrun` (`id` ),
  CONSTRAINT `variable_ptr_id_refs_id_50bf5177`
    FOREIGN KEY (`variable_ptr_id` )
    REFERENCES `autoreduction`.`reduction_variables_variable` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_datalocation`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_datalocation` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `file_path` VARCHAR(255) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `reduction_viewer_datalocation_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_b5530667`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `autoreduction`.`reduction_viewer_reductionrun` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 483
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_notification`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_notification` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `message` VARCHAR(255) NOT NULL ,
  `is_active` TINYINT(1) NOT NULL ,
  `severity` VARCHAR(1) NOT NULL ,
  `is_staff_only` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_reductionlocation`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_reductionlocation` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `file_path` VARCHAR(255) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `reduction_viewer_reductionlocation_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_6404e5b6`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `autoreduction`.`reduction_viewer_reductionrun` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 234
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `autoreduction`.`reduction_viewer_setting`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `autoreduction`.`reduction_viewer_setting` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(50) NOT NULL ,
  `value` VARCHAR(50) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

USE `autoreduction` ;
