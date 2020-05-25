DROP TRIGGER IF EXISTS order_alerts_notify ON order_header;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON order_header
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
  
DROP TRIGGER IF EXISTS order_alerts_notify ON invoicing;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON invoicing
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
  
DROP TRIGGER IF EXISTS order_alerts_notify ON client;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON client
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
  
DROP TRIGGER IF EXISTS order_alerts_notify ON invoicing_line;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON invoicing_line
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
  
DROP TRIGGER IF EXISTS order_alerts_notify ON part_transaction;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON part_transaction
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
  
DROP TRIGGER IF EXISTS order_alerts_notify ON planning_lot_detailed;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON planning_lot_detailed
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();

DROP TRIGGER IF EXISTS order_alerts_notify ON purchase_order_line;
CREATE TRIGGER order_alerts_notify
  AFTER UPDATE OR INSERT OR DELETE
  ON purchase_order_line
  FOR EACH ROW
  EXECUTE PROCEDURE order_alerts_notify();
