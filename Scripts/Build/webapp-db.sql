# Create DB
CREATE DATABASE IF NOT EXISTS webapp;

# Create Schema - generated from current impl

CREATE SCHEMA IF NOT EXISTS `webapp` DEFAULT CHARACTER SET utf8 ;
USE `webapp` ;

-- -----------------------------------------------------
-- Table `webapp`.`autoreduce_webapp_cache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `webapp`.`autoreduce_webapp_cache` (
  `id` INT(11) NOT NULL AUTO_INCREMENT ,
  `created` DATETIME NOT NULL ,
  PRIMARY KEY (`id`) )

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `webapp`.`autoreduce_webapp_experimentcache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `webapp`.`autoreduce_webapp_experimentcache` (
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
    REFERENCES `webapp`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `webapp`.`autoreduce_webapp_instrumentcache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `webapp`.`autoreduce_webapp_instrumentcache` (
  `cache_ptr_id` INT(11) NOT NULL ,
  `id_name` VARCHAR(80) NOT NULL ,
  `upcoming_experiments` LONGTEXT NOT NULL ,
  `valid_experiments` LONGTEXT NOT NULL ,
  PRIMARY KEY (`cache_ptr_id`) ,
  CONSTRAINT `cache_ptr_id_refs_id_6d7bc58e`
    FOREIGN KEY (`cache_ptr_id` )
    REFERENCES `webapp`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `webapp`.`autoreduce_webapp_usercache`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `webapp`.`autoreduce_webapp_usercache` (
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
    REFERENCES `webapp`.`autoreduce_webapp_cache` (`id` ))

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;
