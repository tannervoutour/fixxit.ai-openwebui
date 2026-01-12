import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getLogs = async (
	token: string,
	params: {
		group_id?: string;
		category?: string;
		business_impact?: string;
		verified?: boolean;
		equipment?: string;
		user_filter?: string;
		title_search?: string;
		date_after?: string;
		date_before?: string;
		limit?: number;
		offset?: number;
		sort_by?: string;
		sort_desc?: boolean;
	} = {}
) => {
	let error = null;

	const searchParams = new URLSearchParams();
	
	Object.entries(params).forEach(([key, value]) => {
		if (value !== undefined && value !== null) {
			searchParams.append(key, String(value));
		}
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/logs/?${searchParams.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const createLog = async (
	token: string,
	groupId: string,
	logData: {
		insight_title: string;
		insight_content: string;
		problem_category?: string;
		root_cause?: string;
		solution_steps?: string[];
		tools_required?: string[];
		tags?: string[];
		equipment_group?: string[];
		notes?: string;
	}
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/logs/?group_id=${encodeURIComponent(groupId)}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(logData)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getProblemCategories = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/logs/categories`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getEquipmentGroups = async (token: string, search?: string) => {
	let error = null;

	const searchParams = new URLSearchParams();
	if (search) {
		searchParams.append('search', search);
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/logs/equipment-groups?${searchParams.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getGroupsWithLogs = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/groups/accessible-with-logs`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};