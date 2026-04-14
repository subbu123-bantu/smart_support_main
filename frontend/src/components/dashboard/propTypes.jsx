import PropTypes from "prop-types";

export const statsShape = PropTypes.shape({
  total: PropTypes.number,
  open: PropTypes.number,
  in_progress: PropTypes.number,
  closed: PropTypes.number,
  by_category: PropTypes.arrayOf(
    PropTypes.shape({
      category__name: PropTypes.string,
      count: PropTypes.number,
    })
  ),
  by_priority: PropTypes.arrayOf(
    PropTypes.shape({
      priority: PropTypes.string,
      count: PropTypes.number,
    })
  ),
  by_date: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string,
      count: PropTypes.number,
    })
  ),
  agent_workload: PropTypes.arrayOf(
    PropTypes.shape({
      agent: PropTypes.string,
      assigned: PropTypes.number,
      in_progress: PropTypes.number,
      solved: PropTypes.number,
      avg_resolution_hours: PropTypes.number,
    })
  ),
});

export const ticketShape = PropTypes.shape({
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  priority: PropTypes.string.isRequired,
});

export const agentWorkloadShape = PropTypes.shape({
  agent: PropTypes.string,
  assigned: PropTypes.number,
  in_progress: PropTypes.number,
  solved: PropTypes.number,
  avg_resolution_hours: PropTypes.number,
});

export const pieItemShape = PropTypes.shape({
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
});

export const lineItemShape = PropTypes.shape({
  date: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
});

export const categoryItemShape = PropTypes.shape({
  name: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
});

export const priorityItemShape = PropTypes.shape({
  name: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
});