import { WEBUI_API_BASE_URL } from '$lib/constants';

/**
 * Invitation API functions for managing invitation links
 */

export interface CreateInvitationRequest {
	group_id: string;
	max_uses?: number;
	expires_in_hours?: number;
	note?: string;
}

export interface InvitationResponse {
	id: string;
	group_id: string;
	group_name: string;
	created_by: string;
	token: string;
	invitation_url: string;
	max_uses: number | null;
	current_uses: number;
	expires_at: number | null;
	status: string;
	note: string | null;
	created_at: number;
	updated_at: number;
}

// Create a new invitation link
export const createInvitation = async (token: string, data: CreateInvitationRequest) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/create`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
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

	return res as InvitationResponse;
};

// Get invitations for a specific group
export const getGroupInvitations = async (token: string, groupId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/group/${groupId}`, {
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

	return res as InvitationResponse[];
};

// List all invitations accessible to current user
export const listMyInvitations = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/list`, {
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

	return res as InvitationResponse[];
};

// Revoke an invitation
export const revokeInvitation = async (token: string, invitationId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/${invitationId}/revoke`, {
		method: 'POST',
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

// Delete an invitation
export const deleteInvitation = async (token: string, invitationId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/${invitationId}`, {
		method: 'DELETE',
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

// Validate invitation token (public endpoint)
export const validateInvitation = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/invitations/validate/${token}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
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

	return res as {
		valid: boolean;
		group_id?: string;
		group_name?: string;
		message?: string;
	};
};
