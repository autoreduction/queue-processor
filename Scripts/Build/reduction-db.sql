# Create DB
CREATE DATABASE IF NOT EXISTS reduction;

# Create Schema - generated from current impl

CREATE SCHEMA IF NOT EXISTS `reduction` DEFAULT CHARACTER SET utf8 ;
USE `reduction` ;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_instrument`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_instrument` (
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
-- Table `reduction`.`reduction_variables_variable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_variables_variable` (
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
-- Table `reduction`.`reduction_variables_instrumentvariable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_variables_instrumentvariable` (
  `variable_ptr_id` INT(11) NOT NULL ,
  `instrument_id` INT(11) NOT NULL ,
  `experiment_reference` INT(11) NULL DEFAULT NULL ,
  `start_run` INT(11) NULL DEFAULT NULL ,
  `tracks_script` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`variable_ptr_id`) ,
  INDEX `reduction_variables_instrumentvariable_ce1084cd` (`instrument_id` ASC) ,
  CONSTRAINT `instrument_id_refs_id_b848104d`
    FOREIGN KEY (`instrument_id` )
    REFERENCES `reduction`.`reduction_viewer_instrument` (`id` ),
  CONSTRAINT `variable_ptr_id_refs_id_a230c877`
    FOREIGN KEY (`variable_ptr_id` )
    REFERENCES `reduction`.`reduction_variables_variable` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_experiment`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_experiment` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `reference_number` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 16
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_status`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_status` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `value` VARCHAR(25) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
AUTO_INCREMENT = 6
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_reductionrun`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_reductionrun` (
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
    REFERENCES `reduction`.`reduction_viewer_experiment` (`id` ),
  CONSTRAINT `instrument_id_refs_id_978dd513`
    FOREIGN KEY (`instrument_id` )
    REFERENCES `reduction`.`reduction_viewer_instrument` (`id` ),
  CONSTRAINT `retry_run_id_refs_id_a07852ad`
    FOREIGN KEY (`retry_run_id` )
    REFERENCES `reduction`.`reduction_viewer_reductionrun` (`id` ),
  CONSTRAINT `status_id_refs_id_f353ac8f`
    FOREIGN KEY (`status_id` )
    REFERENCES `reduction`.`reduction_viewer_status` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 492
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_variables_runvariable`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_variables_runvariable` (
  `variable_ptr_id` INT(11) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`variable_ptr_id`) ,
  INDEX `reduction_variables_runvariable_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_7a2c2892`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `reduction`.`reduction_viewer_reductionrun` (`id` ),
  CONSTRAINT `variable_ptr_id_refs_id_50bf5177`
    FOREIGN KEY (`variable_ptr_id` )
    REFERENCES `reduction`.`reduction_variables_variable` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_datalocation`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_datalocation` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `file_path` VARCHAR(255) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `reduction_viewer_datalocation_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_b5530667`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `reduction`.`reduction_viewer_reductionrun` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 483
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_notification`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_notification` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `message` VARCHAR(255) NOT NULL ,
  `is_active` TINYINT(1) NOT NULL ,
  `severity` VARCHAR(1) NOT NULL ,
  `is_staff_only` TINYINT(1) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_reductionlocation`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_reductionlocation` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `file_path` VARCHAR(255) NOT NULL ,
  `reduction_run_id` INT(11) NOT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `reduction_viewer_reductionlocation_6165194e` (`reduction_run_id` ASC) ,
  CONSTRAINT `reduction_run_id_refs_id_6404e5b6`
    FOREIGN KEY (`reduction_run_id` )
    REFERENCES `reduction`.`reduction_viewer_reductionrun` (`id` ))

ENGINE = InnoDB
AUTO_INCREMENT = 234
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `reduction`.`reduction_viewer_setting`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `reduction`.`reduction_viewer_setting` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(50) NOT NULL ,
  `value` VARCHAR(50) NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

USE `reduction` ;
